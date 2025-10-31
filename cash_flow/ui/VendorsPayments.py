from datetime import date, datetime

import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel, QTabWidget, QFrame, \
    QPushButton
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import AccountType
# from cash_flow.database.Model import Document, DocType, Customer
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.ui.ComboDefinition import ComboDefinition


class VendorsPayments(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()

        self.pane_filter = QFrame()
        self.filter_visible = True
        self.btn_filter = QPushButton("Filtrs  (noslēpt)")
        self.btn_filter.setStyleSheet("font-weight: bold")
        self.btn_filter.setMaximumWidth(150)
        self.btn_filter.clicked.connect(self.toggle_filter)
        filterbox = QVBoxLayout()
        filter_line1 = QHBoxLayout()
        filter_line2 = QHBoxLayout()
        filter_line3 = QHBoxLayout()

        label_definition = QLabel("NP Nosaukums")
        self.filter_definition = ComboDefinition(self.engine, allow_empty=True)
        self.filter_definition.currentIndexChanged.connect(self.requery)
        definition = pd.read_sql_query(
            "SELECT id, key, name FROM E01_CashFlowDefinition WHERE definition_type = 1 ORDER BY key",
            self.engine)
        self.dict_definition = dict(zip(definition['name'], definition['id']))
        filter_line1.addWidget(label_definition)
        filter_line1.addWidget(self.filter_definition)

        label_number = QLabel("Numurs")
        self.filter_number = QLineEdit()
        self.filter_number.setMaximumWidth(100)
        self.filter_number.editingFinished.connect(self.requery)
        label_partner = QLabel("Partneris")
        self.filter_partner = QLineEdit()
        self.filter_partner.editingFinished.connect(self.requery)
        filter_line2.addWidget(label_number)
        filter_line2.addWidget(self.filter_number)
        filter_line2.addWidget(label_partner)
        filter_line2.addWidget(self.filter_partner)

        label_date_doc = QLabel("Dokumenta datums")
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setCalendarPopup(True)
        self.filter_date_from.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_date_from.setDate(date(datetime.now().year, 1, 1))
        self.filter_date_from.dateChanged.connect(self.requery)
        self.filter_date_through = QDateEdit()
        self.filter_date_through.setCalendarPopup(True)
        self.filter_date_through.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_date_through.setDate(datetime.now())
        self.filter_date_through.dateChanged.connect(self.requery)
        filter_line3.addWidget(label_date_doc)
        filter_line3.addWidget(self.filter_date_from)
        filter_line3.addWidget(self.filter_date_through)

        filterbox.addLayout(filter_line1)
        filterbox.addLayout(filter_line2)
        filterbox.addLayout(filter_line3)
        self.pane_filter.setLayout(filterbox)

        label_payments = QLabel("Maksājumi")
        label_payments.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(CustomersPaymentsModel(self.table, self.engine))
        self.table.selectionModel().currentRowChanged.connect(self.document_changed)

        self.btn_details = QPushButton("Detaļas  (parādīt)")
        self.btn_details.setStyleSheet("font-weight: bold")
        self.btn_details.setMaximumWidth(150)
        self.btn_details.clicked.connect(self.toggle_details)
        self.pane_details = QFrame()
        self.pane_details.setMaximumHeight(250)
        self.details_visible = False
        box_details = QVBoxLayout()
        tabs_details = QTabWidget()
        self.payment_accounts = ATable()
        self.payment_accounts.setModel(PaymentsCorrespondenceModel(self.payment_accounts, self.engine))
        self.payment_clearing = ATable()
        self.payment_clearing.setModel(PaymentsClearingModel(self.payment_clearing, self.engine))
        tabs_details.addTab(self.payment_accounts, "Kontu koresponence")
        tabs_details.addTab(self.payment_clearing, "Apmaksātie rēķini")
        self.pane_details.setLayout(box_details)
        box_details.addWidget(tabs_details)
        self.pane_details.setVisible(self.details_visible)



        vbox.addWidget(self.btn_filter)
        vbox.addWidget(self.pane_filter)
        vbox.addWidget(label_payments)
        vbox.addWidget(self.table)
        vbox.addWidget(self.btn_details)
        vbox.addWidget(self.pane_details)
        self.setLayout(vbox)

        self.requery()

    def toggle_filter(self):
        self.filter_visible = not self.filter_visible
        self.pane_filter.setVisible(self.filter_visible)
        self.btn_filter.setText("Filtrs  (noslēpt)" if self.filter_visible else "Filtrs  (parādīt)")

    def toggle_details(self):
        self.details_visible = not self.details_visible
        self.pane_details.setVisible(self.details_visible)
        self.btn_details.setText("Detaļas  (noslēpt)" if self.details_visible else "Detaļas  (parādīt)")

    def document_changed(self, index_current, index_previous):
        with self.table.model().lock:
            payment_id = self.table.model().DATA.index[index_current.row()]
        self.payment_accounts.model().set_filter({"payment_id": payment_id})
        self.payment_clearing.model().set_filter({"payment_id": payment_id})

    def requery(self):
        self.table.model().set_filter({"definition_id": self.dict_definition.get(self.filter_definition.currentText()),
                                        "date from": self.filter_date_from.date().toPyDate(),
                                       "date through": self.filter_date_through.date().toPyDate(),
                                       "partner": self.filter_partner.text(),
                                       "number": self.filter_number.text()})
        self.payment_accounts.model().set_filter({})
        self.payment_clearing.model().set_filter({})


class PaymentsCorrespondenceModel(ATableModel):
    def _do_requery(self):
        with self.lock:
            payment_id = self.FILTER.get("payment_id")

        if not payment_id:
            return None

        gl = pd.read_sql_query("SELECT * FROM G08_CashFlow_Actual WHERE d_id = " + str(payment_id), self.engine)
        gl = gl.reindex(columns=["entry_type", "account", "currency", "amount", "amount_LC"])
        gl.columns = ["VG Tips", "VG Konts", "Valūta", "Summa", "Summa BV"]

        return gl


class PaymentsClearingModel(ATableModel):

    def _do_requery(self):
        with self.lock:
            payment_id = self.FILTER.get("payment_id")

        if not payment_id:
            return None

        clearing = pd.read_sql_query(
            "SELECT * FROM H03_Reconciliations_CR WHERE dr_docid = " + str(payment_id), self.engine)
        clearing["date"] = pd.to_datetime(clearing["date"])
        clearing = clearing.reindex(columns=["id", "type_name", "number", "date",
                                             "description", "partner_name",
                                             "r_amount", "currency", "cr_amount"])
        clearing.columns = ["id", "Dok. Tips", "Numurs", "Datums",
                            "Apraksts", "Partneris",
                            "Summa", "Valūta", "Dokumenta Summa"]
        clearing.set_index("id", inplace=True)

        return clearing

class CustomersPaymentsModel(ATableModel):

    def _do_requery(self):

        cash_type = "Payment"

        with self.lock:
            filter_dfrom = pd.to_datetime(self.FILTER.get("date from"))
            filter_dthrough = pd.to_datetime(self.FILTER.get("date through"))
            filter_partner = self.FILTER.get("partner")
            filter_definition = self.FILTER.get("definition_id")
            filter_number = self.FILTER.get("number")

        # Read database
        payments = pd.read_sql_query("SELECT * FROM G03_CashTransactions_Corresponding WHERE cash_type = '" + cash_type + "'", self.engine)

        # Format columns
        payments["date"] = pd.to_datetime(payments["date"])
        payments["date_cleared"] = pd.to_datetime(payments["date_cleared"])
        payments["cleared"] = payments["cleared"].astype(bool)

        payments = payments[(payments["date"] >= filter_dfrom) & (payments["date"] <= filter_dthrough)]

        if filter_partner:
            payments = payments[payments["partner_name"].str.contains(filter_partner, case=False)]

        if filter_number:
            payments = payments[payments["d_number"] == filter_number]

        if filter_definition:
            accounts = pd.read_sql_table("B02_Accounts", self.engine)
            valid_accounts = \
                accounts[~accounts["type_id"].isin([AccountType.CUSTOMERS_ACCOUNT, AccountType.VENDORS_ACCOUNT])]["code"]

            definition = pd.read_sql_table("E01_CashFlowDefinitionAccounts", self.engine)
            definition.drop(columns="id", inplace=True)
            definition = definition[definition["cash_type"] == cash_type]
            definition = definition[definition["definition_id"] == filter_definition]
            definition = definition[definition["account"].isin(valid_accounts)]

            gl = pd.read_sql_table("G09_CashFlow_Actual_Corresponding", self.engine)
            gl = gl[gl["d_id"].isin(payments["d_id"])]
            # print("gl: ", gl)

            filtered_payments = gl[gl["account"].isin(definition["account"])]["d_id"].unique()
            # print("filtered_payments: ", filtered_payments)

            payments = payments[payments["d_id"].isin(filtered_payments)]
            # print("payments: ", payments)

        # Formatting to GUI
        payments["remaining_amount"] = payments["amount"] - payments["cleared_amount"]

        payments.sort_values(["date", "date_cleared", "d_id"],
                             ascending=[False, False, False], na_position="first", inplace=True)

        payments = payments.reindex(columns=["d_id", "d_type", "d_number", "partner_name",
                                             "date", "date_cleared",
                                             "cleared", "d_description",
                                             "amount", "currency", "remaining_amount"])

        payments.columns = ["d_id", "Tips", "Numurs", "Partneris",
                            "Datums", "Dzēšanas datums",
                            "Dzēsts", "Apraksts",
                            "Summa", "Valūta", "Atlikusī summa"]

        payments.set_index("d_id", inplace=True)

        return payments


