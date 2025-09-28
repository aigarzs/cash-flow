from datetime import date, datetime

import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel, QTabWidget
from sqlalchemy import select
from sqlalchemy.orm import Session

# from cash_flow.database.Model import Document, DocType, Customer
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.ui.ComboDefinition import ComboDefinition


class CustomersPayments(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        filterbox = QVBoxLayout()
        filter_line1 = QHBoxLayout()
        filter_line2 = QHBoxLayout()
        filter_line3 = QHBoxLayout()

        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")

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
        label_customer = QLabel("Klients")
        self.filter_customer = QLineEdit()
        self.filter_customer.editingFinished.connect(self.requery)
        filter_line2.addWidget(label_number)
        filter_line2.addWidget(self.filter_number)
        filter_line2.addWidget(label_customer)
        filter_line2.addWidget(self.filter_customer)

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

        label_payments = QLabel("Maksājumi")
        label_payments.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(CustomersPaymentsModel(self.table, self.engine))
        self.table.selectionModel().currentRowChanged.connect(self.document_changed)

        tabs_details = QTabWidget()
        self.payment_accounts = ATable()
        self.payment_accounts.setModel(PaymentsCorrespondenceModel(self.payment_accounts, self.engine))
        self.payment_clearing = ATable()
        self.payment_clearing.setModel(PaymentsClearingModel(self.payment_clearing, self.engine))
        tabs_details.addTab(self.payment_accounts, "Kontu koresponence")
        tabs_details.addTab(self.payment_clearing, "Apmaksātie rēķini")
        tabs_details.setMaximumHeight(250)

        filterbox.addWidget(label_filter)
        filterbox.addLayout(filter_line1)
        filterbox.addLayout(filter_line2)
        filterbox.addLayout(filter_line3)

        vbox.addLayout(filterbox)
        vbox.addWidget(label_payments)
        vbox.addWidget(self.table)
        vbox.addWidget(tabs_details)
        self.setLayout(vbox)

        self.requery()

    def document_changed(self, index_current, index_previous):
        payment_id = self.table.model().DATA.index[index_current.row()]
        self.payment_accounts.model().set_filter({"payment_id": payment_id})
        self.payment_clearing.model().set_filter({"payment_id": payment_id})

    def requery(self):
        self.table.model().set_filter({"definition_id": self.dict_definition.get(self.filter_definition.currentText()),
                                        "date from": self.filter_date_from.date().toPyDate(),
                                       "date through": self.filter_date_through.date().toPyDate(),
                                       "customer": self.filter_customer.text(),
                                       "number": self.filter_number.text()})
        self.payment_accounts.model().set_filter({})
        self.payment_clearing.model().set_filter({})


class PaymentsCorrespondenceModel(ATableModel):
    def _do_requery(self):
        payment_id = self.FILTER.get("payment_id")

        if not payment_id:
            return None

        gl = pd.read_sql_query("SELECT * FROM G09_CashFlow_Actual WHERE d_id = " + str(payment_id), self.engine)
        gl = gl.reindex(columns=["gl_entry_type", "gl_account", "d_currency", "gl_amount", "gl_amount_LC"])
        gl.columns = ["VG Tips", "VG Konts", "Valūta", "Summa", "Summa BV"]

        return gl


class PaymentsClearingModel(ATableModel):

    def _do_requery(self):
        payment_id = self.FILTER.get("payment_id")

        if not payment_id:
            return None

        clearing = pd.read_sql_query(
            "SELECT * FROM H02_Payment_Reconciliations WHERE payment_id = " + str(payment_id), self.engine)
        clearing["i_date"] = pd.to_datetime(clearing["i_date"])
        clearing = clearing.reindex(columns=["id", "i_type_name", "i_number", "i_date",
                                             "i_description", "i_customer_name",
                                             "r_amount", "r_currency", "i_amount", "i_currency"])
        clearing.columns = ["id", "Dok. Tips", "Numurs", "Datums",
                            "Apraksts", "Klients",
                            "Summa", "Valūta", "Dokumenta Summa", "Dokumenta Valūta"]
        clearing.set_index("id", inplace=True)

        return clearing

class CustomersPaymentsModel(ATableModel):

    def _do_requery(self):

        doctype = str(DocType.BANK_RECEIPT)
        cash_type = "Receipt"

        # Read database
        payments = pd.read_sql_query("SELECT * FROM D01_Documents WHERE type_id = " + doctype + "", self.engine)
        doctypes = pd.read_sql_table("D02_DocTypes", self.engine)
        customers = pd.read_sql_query("SELECT id, name FROM B04_Customers", self.engine)

        # Format columns
        payments["date"] = pd.to_datetime(payments["date"])
        payments["date_cleared"] = pd.to_datetime(payments["date_cleared"])
        payments["cleared"] = payments["cleared"].astype(bool)

        filter_dfrom = pd.to_datetime(self.FILTER.get("date from"))
        filter_dthrough = pd.to_datetime(self.FILTER.get("date through"))

        payments = payments[(payments["date"] >= filter_dfrom) & (payments["date"] <= filter_dthrough)]

        # Merge doctypes and customer
        doctypes.rename(columns={"id": "type_id", "name": "type_name"}, inplace=True)
        customers.rename(columns={"id": "customer_id", "name": "customer_name"}, inplace=True)
        payments.rename(columns={"id": "document_id"}, inplace=True)
        payments = pd.merge(payments, doctypes, on="type_id", how="left")
        payments = pd.merge(payments, customers, on="customer_id", how="left")

        filter_customer = self.FILTER.get("customer")
        filter_definition = self.FILTER.get("definition_id")
        filter_number = self.FILTER.get("number")

        if filter_customer:
            payments = payments[payments["customer_name"].str.contains(filter_customer, case=False)]

        if filter_number:
            payments = payments[payments["number"] == filter_number]

        if filter_definition:
            definition = pd.read_sql_table("E01_CashFlowDefinitionAccounts", self.engine)
            definition.drop(columns="id", inplace=True)
            definition = definition[definition["cash_type"] == cash_type]
            definition = definition[definition["definition_id"] == filter_definition]
            # print("definition: ", definition)

            gl = pd.read_sql_table("G10_CashFlow_Actual_Corresponding", self.engine)
            gl = gl[gl["d_id"].isin(payments["document_id"])]
            # print("gl: ", gl)

            filtered_payments = gl[gl["gl_account"].isin(definition["account"])]["d_id"].unique()
            # print("filtered_payments: ", filtered_payments)

            payments = payments[payments["document_id"].isin(filtered_payments)]
            # print("payments: ", payments)

        # Formatting to GUI
        payments["remaining_amount"] = payments["amount"] - payments["cleared_amount"]

        payments.sort_values(["date", "date_cleared", "document_id"],
                             ascending=[False, False, False], na_position="first", inplace=True)

        payments = payments.reindex(columns=["document_id", "type_name", "number", "customer_name",
                                             "date", "date_cleared",
                                             "cleared", "description",
                                             "amount", "currency", "remaining_amount"])

        payments.columns = ["id", "Tips", "Numurs", "Klients",
                            "Datums", "Dzēšanas datums",
                            "Dzēsts", "Apraksts",
                            "Summa", "Valūta", "Atlikusī summa"]

        payments.set_index("id", inplace=True)

        return payments


