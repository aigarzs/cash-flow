from datetime import date, datetime

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel, QComboBox, QCheckBox, \
    QFileDialog, QPushButton, QTabWidget
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Document, DocType, AccountType
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import str_to_date, str_to_priority


class CustomersInvoices(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        filterbox = QVBoxLayout()
        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")

        filterbox_line1 = QHBoxLayout()
        filterbox_line2 = QHBoxLayout()
        filterbox_line3 = QHBoxLayout()
        filterbox_line4 = QHBoxLayout()
        filterbox_line5 = QHBoxLayout()
        filterbox_line6 = QHBoxLayout()

        label_cf_def = QLabel("NP Pozīcija")
        self.filter_cf_definition = QComboBox()
        definition = pd.read_sql_query("SELECT id, key, name FROM E01_CashFlowDefinition WHERE definition_type = 1 ORDER BY key",
                                       self.engine)
        self.filter_cf_definition.addItem("")
        self.filter_cf_definition.addItems(definition["name"])
        self.filter_cf_definition.currentIndexChanged.connect(self.requery)
        self.dict_cf_definition = dict(zip(definition['name'], definition['id']))
        filterbox_line1.addWidget(label_cf_def)
        filterbox_line1.addWidget(self.filter_cf_definition)

        label_number = QLabel("Numurs")
        self.filter_number = QLineEdit()
        self.filter_number.setMaximumWidth(100)
        self.filter_number.editingFinished.connect(self.requery)
        label_customer = QLabel("Klients")
        self.filter_customer = QLineEdit()
        self.filter_customer.editingFinished.connect(self.requery)
        filterbox_line2.addWidget(label_number)
        filterbox_line2.addWidget(self.filter_number)
        filterbox_line2.addWidget(label_customer)
        filterbox_line2.addWidget(self.filter_customer)

        label_docdate = QLabel("Dokumenta datums")
        self.filter_docdate_from = QDateEdit()
        self.filter_docdate_from.setCalendarPopup(True)
        self.filter_docdate_from.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_docdate_from.setDate(date(datetime.now().year, 1, 1))
        self.filter_docdate_from.dateChanged.connect(self.requery)
        self.filter_docdate_from.setEnabled(False)
        self.filter_docdate_through = QDateEdit()
        self.filter_docdate_through.setCalendarPopup(True)
        self.filter_docdate_through.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_docdate_through.setDate(datetime.now())
        self.filter_docdate_through.dateChanged.connect(self.requery)
        self.filter_docdate_through.setEnabled(False)
        self.check_docdate = QCheckBox()
        self.check_docdate.stateChanged.connect(self.toggle_docdate)
        filterbox_line3.addWidget(label_docdate)
        filterbox_line3.addWidget(self.check_docdate)
        filterbox_line3.addWidget(self.filter_docdate_from)
        filterbox_line3.addWidget(self.filter_docdate_through)

        label_duedate = QLabel("Apmaksas termiņš")
        self.filter_duedate_from = QDateEdit()
        self.filter_duedate_from.setCalendarPopup(True)
        self.filter_duedate_from.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_duedate_from.setDate(date(datetime.now().year, 1, 1))
        self.filter_duedate_from.dateChanged.connect(self.requery)
        self.filter_duedate_from.setEnabled(False)
        self.filter_duedate_through = QDateEdit()
        self.filter_duedate_through.setCalendarPopup(True)
        self.filter_duedate_through.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_duedate_through.setDate(datetime.now())
        self.filter_duedate_through.dateChanged.connect(self.requery)
        self.filter_duedate_through.setEnabled(False)
        self.check_duedate = QCheckBox()
        self.check_duedate.stateChanged.connect(self.toggle_duedate)
        filterbox_line4.addWidget(label_duedate)
        filterbox_line4.addWidget(self.check_duedate)
        filterbox_line4.addWidget(self.filter_duedate_from)
        filterbox_line4.addWidget(self.filter_duedate_through)

        label_planneddate = QLabel("Plānots datums")
        self.filter_planneddate_from = QDateEdit()
        self.filter_planneddate_from.setCalendarPopup(True)
        self.filter_planneddate_from.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_planneddate_from.setDate(date(datetime.now().year, 1, 1))
        self.filter_planneddate_from.dateChanged.connect(self.requery)
        self.filter_planneddate_from.setEnabled(False)
        self.filter_planneddate_through = QDateEdit()
        self.filter_planneddate_through.setCalendarPopup(True)
        self.filter_planneddate_through.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_planneddate_through.setDate(datetime.now())
        self.filter_planneddate_through.dateChanged.connect(self.requery)
        self.filter_planneddate_through.setEnabled(False)
        self.check_planneddate = QCheckBox()
        self.check_planneddate.stateChanged.connect(self.toggle_planneddate)
        filterbox_line5.addWidget(label_planneddate)
        filterbox_line5.addWidget(self.check_planneddate)
        filterbox_line5.addWidget(self.filter_planneddate_from)
        filterbox_line5.addWidget(self.filter_planneddate_through)

        label_cleareddate = QLabel("Apmaksas datums")
        self.filter_cleareddate_from = QDateEdit()
        self.filter_cleareddate_from.setCalendarPopup(True)
        self.filter_cleareddate_from.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_cleareddate_from.setDate(date(datetime.now().year, 1, 1))
        self.filter_cleareddate_from.dateChanged.connect(self.requery)
        self.filter_cleareddate_from.setEnabled(False)
        self.filter_cleareddate_through = QDateEdit()
        self.filter_cleareddate_through.setCalendarPopup(True)
        self.filter_cleareddate_through.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_cleareddate_through.setDate(datetime.now())
        self.filter_cleareddate_through.dateChanged.connect(self.requery)
        self.filter_cleareddate_through.setEnabled(False)
        self.check_cleareddate = QCheckBox()
        self.check_cleareddate.stateChanged.connect(self.toggle_cleareddate)
        filterbox_line6.addWidget(label_cleareddate)
        filterbox_line6.addWidget(self.check_cleareddate)
        filterbox_line6.addWidget(self.filter_cleareddate_from)
        filterbox_line6.addWidget(self.filter_cleareddate_through)

        filterbox.addWidget(label_filter)
        filterbox.addLayout(filterbox_line1)
        filterbox.addLayout(filterbox_line2)
        filterbox.addLayout(filterbox_line3)
        filterbox.addLayout(filterbox_line4)
        filterbox.addLayout(filterbox_line5)
        filterbox.addLayout(filterbox_line6)

        commandsbox = QHBoxLayout()
        label_invoices = QLabel("Rēķini")
        label_invoices.setStyleSheet("font-weight: bold")
        btn_excel = QPushButton("Eksportēt uz Excel")
        btn_excel.clicked.connect(self.export_to_excel)
        commandsbox.addWidget(label_invoices)
        commandsbox.addStretch()
        commandsbox.addWidget(btn_excel)

        self.invoice_accounts = ATable()
        self.invoice_accounts.setModel(InvoiceAccountsModel(self.invoice_accounts, self.engine))

        self.invoice_clearing = ATable()
        self.invoice_clearing.setModel(InvoiceClearingModel(self.invoice_clearing, self.engine))

        tabs_details = QTabWidget()
        tabs_details.setMaximumHeight(250)
        tabs_details.addTab(self.invoice_accounts, "Kontējumi")
        tabs_details.addTab(self.invoice_clearing, "Apmaksa")

        self.table = ATable()
        self.table.setModel(CustomersInvoicesModel(self.table, self.engine))
        self.table.selectionModel().currentRowChanged.connect(self.invoice_changed)

        vbox.addLayout(filterbox)
        vbox.addLayout(commandsbox)
        vbox.addWidget(self.table)
        vbox.addWidget(tabs_details)
        self.setLayout(vbox)

        self.check_docdate.setChecked(True)

        # self.check_docdate.setChecked(True) toggle calls requery
        # self.requery()

    def invoice_changed(self, index_current, index_previous):
        invoice_id = self.table.model().DATA.index[index_current.row()]
        self.invoice_accounts.model().set_filter({"invoice_id": invoice_id})
        self.invoice_clearing.model().set_filter({"invoice_id": invoice_id})


    def toggle_docdate(self, state):
        if state == Qt.CheckState.Checked.value:
            self.filter_docdate_from.setEnabled(True)
            self.filter_docdate_through.setEnabled(True)
        else:
            self.filter_docdate_from.setEnabled(False)
            self.filter_docdate_through.setEnabled(False)

        self.requery()


    def toggle_duedate(self, state):
        if state == Qt.CheckState.Checked.value:
            self.filter_duedate_from.setEnabled(True)
            self.filter_duedate_through.setEnabled(True)
        else:
            self.filter_duedate_from.setEnabled(False)
            self.filter_duedate_through.setEnabled(False)

        self.requery()


    def toggle_planneddate(self, state):
        if state == Qt.CheckState.Checked.value:
            self.filter_planneddate_from.setEnabled(True)
            self.filter_planneddate_through.setEnabled(True)
        else:
            self.filter_planneddate_from.setEnabled(False)
            self.filter_planneddate_through.setEnabled(False)

        self.requery()


    def toggle_cleareddate(self, state):
        if state == Qt.CheckState.Checked.value:
            self.filter_cleareddate_from.setEnabled(True)
            self.filter_cleareddate_through.setEnabled(True)
        else:
            self.filter_cleareddate_from.setEnabled(False)
            self.filter_cleareddate_through.setEnabled(False)

        self.requery()


    def export_to_excel(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)")

        if file_name:
            if not file_name.endswith(".xlsx"):
                file_name += ".xlsx"
            # Save DataFrame to Excel
            self.table.model().DATA.to_excel(file_name, index=True)


    def requery(self):
        filter = {"definition_id": self.dict_cf_definition.get(self.filter_cf_definition.currentText(), 0),
                  "customer": self.filter_customer.text(),
                  "number": self.filter_number.text()}

        if self.check_docdate.isChecked():
            filter["filter docdate"] = True
            filter["docdate from"] = self.filter_docdate_from.date().toPyDate()
            filter["docdate through"] = self.filter_docdate_through.date().toPyDate()

        if self.check_duedate.isChecked():
            filter["filter duedate"] = True
            filter["duedate from"] = self.filter_duedate_from.date().toPyDate()
            filter["duedate through"] = self.filter_duedate_through.date().toPyDate()

        if self.check_planneddate.isChecked():
            filter["filter planneddate"] = True
            filter["planneddate from"] = self.filter_planneddate_from.date().toPyDate()
            filter["planneddate through"] = self.filter_planneddate_through.date().toPyDate()

        if self.check_cleareddate.isChecked():
            filter["filter cleareddate"] = True
            filter["cleareddate from"] = self.filter_cleareddate_from.date().toPyDate()
            filter["cleareddate through"] = self.filter_cleareddate_through.date().toPyDate()


        self.table.model().set_filter(filter)
        self.invoice_accounts.model().set_filter({})
        self.invoice_clearing.model().set_filter({})


class InvoiceAccountsModel(ATableModel):
    def _do_requery(self):
        invoice_id = self.FILTER.get("invoice_id")

        if not invoice_id:
            return None

        gl = pd.read_sql_query("SELECT * FROM D03_GeneralLedger WHERE document_id = " + str(invoice_id), self.engine)
        invoice = pd.read_sql_query("SELECT id AS document_id, currency FROM D01_Documents WHERE id = " + str(invoice_id), self.engine)

        gl = pd.merge(gl, invoice, on="document_id", how="left")
        gl = gl.reindex(columns=["id", "entry_type", "account", "amount", "currency", "amount_LC"])
        gl.columns = ["id", "VG Tips", "VG Konts", "Summa", "Valūta", "Summa BV"]
        gl.set_index("id", inplace=True)
        return gl



class InvoiceClearingModel(ATableModel):
    def _do_requery(self):
        invoice_id = self.FILTER.get("invoice_id")

        if not invoice_id:
            return None

        clearing = pd.read_sql_query("SELECT * FROM H01_Invoice_Reconciliations WHERE invoice_id = " + str(invoice_id), self.engine)
        clearing["p_date"] = pd.to_datetime(clearing["p_date"])
        clearing = clearing.reindex(columns=["id", "p_type_name", "p_number", "p_date",
                                             "p_description", "p_customer_name",
                                             "r_amount", "r_currency", "p_amount", "p_currency"])
        clearing.columns = ["id", "Dok. Tips", "Numurs", "Datums",
                            "Apraksts", "Klients",
                            "Summa", "Valūta", "Dokumenta Summa", "Dokumenta Valūta"]
        clearing.set_index("id", inplace=True)

        return clearing

class CustomersInvoicesModel(ATableModel):

    def _do_requery(self):

        # Customer Invoices and Creditnotes
        doctypes = str((DocType.INVOICE_CUSTOMER, DocType.CREDITNOTE_CUSTOMER))
        cash_type = "Receipt"

        #Read database
        invoices = pd.read_sql_query("SELECT * FROM D01_Documents WHERE type_id IN " + doctypes + "", self.engine)
        doctypes = pd.read_sql_table("D02_DocTypes", self.engine)
        customers = pd.read_sql_query("SELECT id, name FROM B04_Customers", self.engine)

        # Format columns
        invoices["date"] = pd.to_datetime(invoices["date"])
        invoices["date_due"] = pd.to_datetime(invoices["date_due"])
        invoices["date_planned_clearing"] = pd.to_datetime(invoices["date_planned_clearing"])
        invoices["date_cleared"] = pd.to_datetime(invoices["date_cleared"])
        invoices["cleared"] = invoices["cleared"].astype(bool)
        invoices["void"] = invoices["void"].astype(bool)

        if self.FILTER.get("filter docdate"):
            dfrom = pd.to_datetime(self.FILTER.get("docdate from"))
            dthrough = pd.to_datetime(self.FILTER.get("docdate through"))
            invoices = invoices[(invoices["date"] >= dfrom) & (invoices["date"] <= dthrough)]

        if self.FILTER.get("filter duedate"):
            dfrom = pd.to_datetime(self.FILTER.get("duedate from"))
            dthrough = pd.to_datetime(self.FILTER.get("duedate through"))
            invoices = invoices[(invoices["date_due"] >= dfrom) & (invoices["date_due"] <= dthrough)]

        if self.FILTER.get("filter planneddate"):
            dfrom = pd.to_datetime(self.FILTER.get("planneddate from"))
            dthrough = pd.to_datetime(self.FILTER.get("planneddate through"))
            invoices = invoices[(invoices["date_planned_clearing"] >= dfrom) & (invoices["date_planned_clearing"] <= dthrough)]

        if self.FILTER.get("filter cleareddate"):
            dfrom = pd.to_datetime(self.FILTER.get("cleareddate from"))
            dthrough = pd.to_datetime(self.FILTER.get("cleareddate through"))
            invoices = invoices[(invoices["date_cleared"] >= dfrom) & (invoices["date_cleared"] <= dthrough)]

        # Merge doctypes and customer
        doctypes.rename(columns={"id": "type_id", "name": "type_name"}, inplace=True)
        customers.rename(columns={"id": "customer_id", "name": "customer_name"}, inplace=True)
        invoices.rename(columns={"id": "document_id"}, inplace=True)
        invoices = pd.merge(invoices, doctypes, on="type_id", how="left")
        invoices = pd.merge(invoices, customers, on="customer_id", how="left")

        filter_customer = self.FILTER.get("customer")
        filter_definition = self.FILTER.get("definition_id")
        filter_number = self.FILTER.get("number")

        if filter_customer:
            invoices = invoices[invoices["customer_name"].str.contains(filter_customer, case=False)]

        if filter_number:
            invoices = invoices[invoices["number"] == filter_number]

        if filter_definition:
            accounts = pd.read_sql_table("B02_Accounts", self.engine)
            operation_accounts = accounts[accounts["type_id"].isin([AccountType.EXPENSES_ACCOUNT, AccountType.REVENUES_ACCOUNT])]["code"]

            definition = pd.read_sql_table("E01_CashFlowDefinitionAccounts", self.engine)
            definition.drop(columns="id", inplace=True)
            definition = definition[definition["cash_type"] == cash_type]
            definition = definition[definition["definition_id"] == filter_definition]
            definition = definition[definition["account"].isin(operation_accounts)]

            gl = pd.read_sql_table("D03_GeneralLedger", self.engine)
            gl = gl[gl["document_id"].isin(invoices["document_id"])]
            filtered_invoices = gl[gl["account"].isin(definition["account"])]["document_id"].unique()
            invoices = invoices[invoices["document_id"].isin(filtered_invoices)]

        # Formatting to GUI
        invoices["remaining_amount"] = invoices["amount"] - invoices["cleared_amount"]

        invoices.sort_values(["date_cleared", "date_due", "date", "document_id"],
                             ascending=[False, False, False, False], na_position="first", inplace=True)

        invoices = invoices.reindex(columns=["document_id", "type_name", "number", "customer_name",
                                                 "date", "date_due", "date_planned_clearing", "date_cleared",
                                                "cleared", "description",
                                                "amount", "currency", "remaining_amount",
                                                "priority", "void", "memo"])

        invoices.columns = ["id", "Tips", "Numurs", "Klients",
                           "Datums", "Apm. termiņš", "Plānotais datums", "Apm. datums",
                            "Apmaksāts", "Apraksts",
                            "Summa", "Valūta", "Atlikusī summa",
                            "Prioritāte", "Anulēts", "Piezīmes"]

        invoices.set_index("id", inplace=True)

        return invoices


    def flags(self, index):
        cleared_column_index = self.get_column_index("Apmaksāts")
        cleared = self.DATA.iloc[index.row(), cleared_column_index]

        if cleared:
            return super().flags(index)
        elif index.column() == self.get_column_index("Piezīmes") or \
                index.column() == self.get_column_index("Plānotais datums") or \
                index.column() == self.get_column_index("Prioritāte"):
            return Qt.ItemFlag.ItemIsEditable | super().flags(index)
        elif index.column() == self.get_column_index("Anulēts"):
            return Qt.ItemFlag.ItemIsUserCheckable | super().flags(index)
        else:
            return super().flags(index)


    def _cast_input_to_value(self, index, value):
        if index.column() == self.get_column_index("Piezīmes"):
            return value
        elif index.column() == self.get_column_index("Plānotais datums"):
            return str_to_date(value)
        elif index.column() == self.get_column_index("Prioritāte"):
            return str_to_priority(value)
        elif index.column() == self.get_column_index("Anulēts"):
            return value == "true"
        else:
            return str(value)

    def _set_data_in_database(self, index, value):
        doc_id = int(self.DATA.index[index.row()])
        stmt_doc = select(Document).where(Document.id == doc_id)

        with Session(self.engine) as session:
            doc = session.scalars(stmt_doc).first()
            if index.column() == self.get_column_index("Piezīmes"):
                doc.memo = value
            elif index.column() == self.get_column_index("Plānotais datums"):
                doc.date_planned_clearing = value
            elif index.column() == self.get_column_index("Prioritāte"):
                doc.priority = value
            elif index.column() == self.get_column_index("Anulēts"):
                doc.void = value

            session.commit()