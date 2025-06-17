from datetime import date, datetime

import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel, QTabWidget
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Document, DocType, Customer
from cash_flow.ui.AWidgets import ATable, ATableModel


class CustomersPayments(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        filterbox = QVBoxLayout()
        filter_line1 = QHBoxLayout()
        filter_line2 = QHBoxLayout()

        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")

        label_number = QLabel("Numurs")
        self.filter_number = QLineEdit()
        self.filter_number.setMaximumWidth(100)
        self.filter_number.editingFinished.connect(self.requery)
        label_customer = QLabel("Klients")
        self.filter_customer = QLineEdit()
        self.filter_customer.editingFinished.connect(self.requery)
        filter_line1.addWidget(label_number)
        filter_line1.addWidget(self.filter_number)
        filter_line1.addWidget(label_customer)
        filter_line1.addWidget(self.filter_customer)

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
        filter_line2.addWidget(label_date_doc)
        filter_line2.addWidget(self.filter_date_from)
        filter_line2.addWidget(self.filter_date_through)

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
        self.table.model().set_filter({"date from": self.filter_date_from.date().toPyDate(),
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

        stmt = select(Document.id,
                      DocType.name,
                      Document.number,
                      Customer.name,
                      Document.date,
                      Document.amount,
                      Document.currency
                      ) \
            .join(DocType) \
            .join(Customer) \
            .where(Document.type_id == DocType.BANK_RECEIPT) \
            .order_by(Document.date, Customer.name, Document.id)

        if self.FILTER.get("date from"):
            stmt = stmt.filter(Document.date >= self.FILTER.get("date from"))
        if self.FILTER.get("date through"):
            stmt = stmt.filter(Document.date <= self.FILTER.get("date through"))
        if self.FILTER.get("number"):
            stmt = stmt.filter(Document.number == self.FILTER.get("number"))
        if self.FILTER.get("customer"):
            stmt = stmt.filter(Customer.name.like(f"%{self.FILTER.get('customer')}%"))

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            df = pd.DataFrame(dataset, columns=["id", "Tips", "Numurs", "Klients", "Datums",
                                                       "Summa", "Valūta"])
            df.set_index("id", inplace=True)

        return df



