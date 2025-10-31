from datetime import date, datetime

import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel, QComboBox, QCheckBox, \
    QFileDialog, QPushButton, QTabWidget, QFrame
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Document, DocType, AccountType, GeneralLedger_preserved
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.ui.ComboDefinition import ComboDefinition
from cash_flow.util.Converters import str_to_date, str_to_priority


class CustomersInvoices(QWidget):
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

        filterbox_line1 = QHBoxLayout()
        filterbox_line2 = QHBoxLayout()
        filterbox_line3 = QHBoxLayout()
        filterbox_line4 = QHBoxLayout()
        filterbox_line5 = QHBoxLayout()
        filterbox_line6 = QHBoxLayout()
        filterbox_line7 = QHBoxLayout()

        label_cf_def = QLabel("NP Pozīcija")
        self.filter_cf_definition = ComboDefinition(self.engine, allow_empty=True)
        self.filter_cf_definition.currentIndexChanged.connect(self.requery)
        definition = pd.read_sql_query("SELECT id, key, name FROM E01_CashFlowDefinition WHERE definition_type = 1 ORDER BY key",
                                       self.engine)
        self.dict_cf_definition = dict(zip(definition['name'], definition['id']))
        filterbox_line1.addWidget(label_cf_def)
        filterbox_line1.addWidget(self.filter_cf_definition)

        label_number = QLabel("Numurs")
        self.filter_number = QLineEdit()
        self.filter_number.setMaximumWidth(100)
        self.filter_number.editingFinished.connect(self.requery)
        label_partner = QLabel("Partneris")
        self.filter_partner = QLineEdit()
        self.filter_partner.editingFinished.connect(self.requery)
        filterbox_line2.addWidget(label_number)
        filterbox_line2.addWidget(self.filter_number)
        filterbox_line2.addWidget(label_partner)
        filterbox_line2.addWidget(self.filter_partner)

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

        label_filter_cleared = QLabel("Filtrēt apmaksātos")
        self.filter_cleared = QComboBox()
        self.filter_cleared.addItem("Rādīt visus")
        self.filter_cleared.addItem("Filtrēt apmaksātos")
        self.filter_cleared.addItem("Filtrēt neapmaksātos")
        self.filter_cleared.setCurrentIndex(0)
        self.filter_cleared.currentIndexChanged.connect(self.requery)
        label_filter_void = QLabel("Filtrēt anulētos")
        self.filter_void = QComboBox()
        self.filter_void.addItem("Rādīt visus")
        self.filter_void.addItem("Filtrēt anulētos")
        self.filter_void.addItem("Filtrēt neanulētos")
        self.filter_void.setCurrentIndex(0)
        self.filter_void.currentIndexChanged.connect(self.requery)
        filterbox_line7.addWidget(label_filter_cleared)
        filterbox_line7.addWidget(self.filter_cleared)
        filterbox_line7.addWidget(label_filter_void)
        filterbox_line7.addWidget(self.filter_void)

        filterbox = QVBoxLayout()
        self.pane_filter.setLayout(filterbox)
        filterbox.addLayout(filterbox_line1)
        filterbox.addLayout(filterbox_line2)
        filterbox.addLayout(filterbox_line3)
        filterbox.addLayout(filterbox_line4)
        filterbox.addLayout(filterbox_line5)
        filterbox.addLayout(filterbox_line6)
        filterbox.addLayout(filterbox_line7)

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

        self.btn_details = QPushButton("Detaļas  (parādīt)")
        self.btn_details.setStyleSheet("font-weight: bold")
        self.btn_details.setMaximumWidth(150)
        self.btn_details.clicked.connect(self.toggle_details)
        self.pane_details = QFrame()
        self.pane_details.setMaximumHeight(250)
        self.details_visible = False
        box_details = QVBoxLayout()
        tabs_details = QTabWidget()
        tabs_details.addTab(self.invoice_accounts, "Kontējumi")
        tabs_details.addTab(self.invoice_clearing, "Apmaksa")
        self.pane_details.setLayout(box_details)
        box_details.addWidget(tabs_details)
        self.pane_details.setVisible(self.details_visible)

        self.table = ATable()
        self.table.setModel(CustomersInvoicesModel(self.table, self.engine))
        self.table.selectionModel().currentRowChanged.connect(self.invoice_changed)

        vbox.addWidget(self.btn_filter)
        vbox.addWidget(self.pane_filter)
        vbox.addLayout(commandsbox)
        vbox.addWidget(self.table)
        vbox.addWidget(self.btn_details)
        vbox.addWidget(self.pane_details)
        self.setLayout(vbox)

        self.check_docdate.setChecked(True)

        # self.check_docdate.setChecked(True) toggle calls requery
        # self.requery()

    def invoice_changed(self, index_current, index_previous):
        lock = self.table.model().lock
        with lock:
            invoice_id = self.table.model().DATA.index[index_current.row()]
        self.invoice_accounts.model().set_filter({"invoice_id": invoice_id})
        self.invoice_clearing.model().set_filter({"invoice_id": invoice_id})


    def toggle_filter(self):
        self.filter_visible = not self.filter_visible
        self.pane_filter.setVisible(self.filter_visible)
        self.btn_filter.setText("Filtrs  (noslēpt)" if self.filter_visible else "Filtrs  (parādīt)")

    def toggle_details(self):
        self.details_visible = not self.details_visible
        self.pane_details.setVisible(self.details_visible)
        self.btn_details.setText("Detaļas  (noslēpt)" if self.details_visible else "Detaļas  (parādīt)")

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
                  "partner": self.filter_partner.text(),
                  "number": self.filter_number.text(),
                  "cleared": self.filter_cleared.currentText(),
                  "void": self.filter_void.currentText()}

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
        with self.lock:
            invoice_id = self.FILTER.get("invoice_id")

        if not invoice_id:
            return None

        gl = pd.read_sql_query("SELECT * FROM D03_GeneralLedger WHERE document_id = " + str(invoice_id), self.engine)

        gl = gl.reindex(columns=["id", "entry_type", "account", "amount", "currency", "amount_LC"])
        gl.columns = ["id", "VG Tips", "VG Konts", "Summa", "Valūta", "Summa BV"]
        gl.set_index("id", inplace=True)
        return gl



class InvoiceClearingModel(ATableModel):
    def _do_requery(self):
        with self.lock:
            invoice_id = self.FILTER.get("invoice_id")

        if not invoice_id:
            return None

        clearing = pd.read_sql_query("SELECT * FROM H03_Reconciliations_CR WHERE dr_docid = " + str(invoice_id), self.engine)
        clearing["date"] = pd.to_datetime(clearing["date"])
        clearing = clearing.reindex(columns=["cr_docid", "type_name", "number", "date",
                                             "description", "partner_name",
                                             "r_amount", "currency", "cr_amount"])
        clearing.columns = ["cr_docid", "Dok. Tips", "Numurs", "Datums",
                            "Apraksts", "Partneris",
                            "Summa", "Valūta", "Dokumenta Summa"]
        clearing.set_index("cr_docid", inplace=True)

        return clearing

class CustomersInvoicesModel(ATableModel):

    def _do_requery(self):
        # Customer Invoices and Creditnotes
        acctype = str(AccountType.CUSTOMERS_ACCOUNT)
        cash_type = "Receipt"

        with self.lock:
            filter = self.FILTER.copy()

        #Read database
        invoices = pd.read_sql_query("SELECT * FROM H01_Documents_Pending WHERE gl_account_type = " + acctype + "", self.engine)

        # Format columns
        invoices["date"] = pd.to_datetime(invoices["date"])
        invoices["date_due"] = pd.to_datetime(invoices["date_due"])
        invoices["p_date"] = pd.to_datetime(invoices["p_date"], format="mixed")
        invoices["date_cleared"] = pd.to_datetime(invoices["date_cleared"])
        invoices["cleared"] = invoices["cleared"].astype(bool)
        invoices["void"] = invoices["void"].fillna(False)
        invoices["void"] = invoices["void"].infer_objects(copy=False).astype(bool)
        invoices["priority"] = invoices["priority"].fillna(100)
        invoices["priority"] = invoices["priority"].infer_objects(copy=False).astype(int)


        if filter.get("filter docdate"):
            dfrom = pd.to_datetime(filter.get("docdate from"))
            dthrough = pd.to_datetime(filter.get("docdate through"))
            invoices = invoices[(invoices["date"] >= dfrom) & (invoices["date"] <= dthrough)]

        if filter.get("filter duedate"):
            dfrom = pd.to_datetime(filter.get("duedate from"))
            dthrough = pd.to_datetime(filter.get("duedate through"))
            invoices = invoices[(invoices["date_due"] >= dfrom) & (invoices["date_due"] <= dthrough)]

        if filter.get("filter planneddate"):
            dfrom = pd.to_datetime(filter.get("planneddate from"))
            dthrough = pd.to_datetime(filter.get("planneddate through"))
            invoices = invoices[(invoices["p_date"] >= dfrom) & (invoices["p_date"] <= dthrough)]

        if filter.get("filter cleareddate"):
            dfrom = pd.to_datetime(filter.get("cleareddate from"))
            dthrough = pd.to_datetime(filter.get("cleareddate through"))
            invoices = invoices[(invoices["date_cleared"] >= dfrom) & (invoices["date_cleared"] <= dthrough)]

        filter_partner = filter.get("partner")
        filter_definition = filter.get("definition_id")
        filter_number = filter.get("number")
        filter_cleared = filter.get("cleared")
        filter_void = filter.get("void")

        if filter_partner:
            invoices = invoices[invoices["partner_name"].str.contains(filter_partner, case=False)]

        if filter_number:
            invoices = invoices[invoices["number"] == filter_number]

        if filter_definition:
            accounts = pd.read_sql_table("B02_Accounts", self.engine)
            valid_accounts = \
            accounts[~accounts["type_id"].isin([AccountType.CUSTOMERS_ACCOUNT, AccountType.VENDORS_ACCOUNT])]["code"]

            definition = pd.read_sql_table("E01_CashFlowDefinitionAccounts", self.engine)
            definition.drop(columns="id", inplace=True)
            definition = definition[definition["cash_type"] == cash_type]
            definition = definition[definition["definition_id"] == filter_definition]
            definition = definition[definition["account"].isin(valid_accounts)]

            gl = pd.read_sql_table("D03_GeneralLedger", self.engine)
            gl = gl[gl["document_id"].isin(invoices["d_id"])]
            filtered_invoices = gl[gl["account"].isin(definition["account"])]["document_id"].unique()
            invoices = invoices[invoices["d_id"].isin(filtered_invoices)]

        if filter_cleared == "Filtrēt apmaksātos":
            invoices = invoices[invoices["cleared"] == True]
        elif filter_cleared == "Filtrēt neapmaksātos":
            invoices = invoices[invoices["cleared"] == False]

        if filter_void == "Filtrēt anulētos":
            invoices = invoices[invoices["void"] == True]
        elif filter_void == "Filtrēt neanulētos":
            invoices = invoices[invoices["void"] == False]

        # Formatting to GUI
        invoices.sort_values(["date_cleared", "p_date", "date_due", "date", "d_id"],
                             ascending=[False, False, False, False, False], na_position="first", inplace=True)

        invoices = invoices.reindex(columns=["d_id", "d_type", "number", "partner_id", "partner_name",
                                                  "date", "date_due", "p_date", "date_cleared",
                                                "cleared", "description",
                                                "gl_account", "amount", "currency", "remaining_amount",
                                                "priority", "void", "memo"])

        invoices.columns = ["d_id", "Tips", "Numurs", "Partnera id", "Partneris",
                           "Datums", "Apm. termiņš", "Plānotais datums", "Apm. datums",
                            "Apmaksāts", "Apraksts",
                            "Konts", "Summa", "Valūta", "Atlikusī summa",
                            "Prioritāte", "Anulēts", "Piezīmes"]

        invoices.set_index("d_id", inplace=True)

        return invoices
        # return pd.DataFrame({})

    def _get_flags(self, index):
        cleared_column_index = self.get_column_index("Apmaksāts")
        with self.lock:
            try :
                cleared = self.DATA.iloc[index.row(), cleared_column_index]
            except Exception as err:
                cleared = False

        if cleared:
            return QAbstractTableModel.flags(self, index)
        elif index.column() == self.get_column_index("Piezīmes") or \
                index.column() == self.get_column_index("Plānotais datums") or \
                index.column() == self.get_column_index("Prioritāte"):
            return Qt.ItemFlag.ItemIsEditable | QAbstractTableModel.flags(self, index)
        elif index.column() == self.get_column_index("Anulēts"):
            return Qt.ItemFlag.ItemIsUserCheckable | QAbstractTableModel.flags(self, index)
        else:
            return QAbstractTableModel.flags(self, index)


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
        try:
            partner_id_index = self.get_column_index("Partnera id")
            account_index = self.get_column_index("Konts")
            currency_index = self.get_column_index("Valūta")

            with self.lock:
                document_id = int(self.DATA.index[index.row()])
                partner_id = int(self.DATA.iloc[index.row(), partner_id_index])
                account = self.DATA.iloc[index.row(), account_index]
                currency = self.DATA.iloc[index.row(), currency_index]

            stmt_gl = select(GeneralLedger_preserved).where(
                GeneralLedger_preserved.document_id == document_id,
                GeneralLedger_preserved.partner_id == partner_id,
                GeneralLedger_preserved.account==account,
                GeneralLedger_preserved.currency==currency
            )

            with Session(self.engine) as session:
                preserved = session.scalars(stmt_gl).first()
                if not preserved:
                    preserved = GeneralLedger_preserved(
                        document_id=document_id,
                        partner_id=partner_id,
                        account=account,
                        currency=currency
                    )
                    session.add(preserved)
                    session.commit()

                if index.column() == self.get_column_index("Piezīmes"):
                    preserved.memo = value
                elif index.column() == self.get_column_index("Plānotais datums"):
                    preserved.date_planned_clearing = value
                elif index.column() == self.get_column_index("Prioritāte"):
                    preserved.priority = value
                elif index.column() == self.get_column_index("Anulēts"):
                    preserved.void = value

                session.commit()
                self.logger.info(f"Document {document_id} '{self.get_column_name(index.column())}' set value : {value}")

        except Exception as err:
            self.logger.error(str(err))
