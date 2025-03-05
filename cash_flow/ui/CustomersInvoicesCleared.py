from datetime import date, datetime

import pandas as pd
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Document, DocType, Customer
from cash_flow.ui.AWidgets import ATable, ATableModel


class CustomersInvoicesCleared(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        filterbox = QHBoxLayout()
        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")
        label_customer = QLabel("Klients")
        self.filter_customer = QLineEdit()
        self.filter_customer.editingFinished.connect(self.requery)
        label_date_planned = QLabel("Plānotais datums")
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
        filterbox.addWidget(label_customer)
        filterbox.addWidget(self.filter_customer)
        filterbox.addWidget(label_date_planned)
        filterbox.addWidget(self.filter_date_from)
        filterbox.addWidget(self.filter_date_through)
        label_invoices = QLabel("Rēķini")
        label_invoices.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(CustomersInvoicesClearedModel(self.table, self.engine))

        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox)
        vbox.addWidget(label_invoices)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        self.table.model().set_filter({"date from": self.filter_date_from.date().toPyDate(),
                                       "date through": self.filter_date_through.date().toPyDate(),
                                       "customer": self.filter_customer.text()})


class CustomersInvoicesClearedModel(ATableModel):

    def requery(self):
        self.beginResetModel()

        stmt = select(Document.id,
                      DocType.name,
                      Document.number,
                      Customer.name,
                      Document.date,
                      Document.date_due,
                      Document.date_cleared,
                      Document.amount,
                      Document.currency,
                      Document.priority,
                      Document.memo) \
            .join(DocType) \
            .join(Customer) \
            .where(Document.type_id == DocType.INVOICE_CUSTOMER,
                   Document.cleared == True) \
            .order_by(Document.date_cleared, Customer.name, Document.date_due, Document.id)

        if self.FILTER.get("date from"):
            stmt = stmt.filter(Document.date_cleared >= self.FILTER.get("date from"))
        if self.FILTER.get("date through"):
            stmt = stmt.filter(Document.date_cleared <= self.FILTER.get("date through"))
        if self.FILTER.get("customer"):
            stmt = stmt.filter(Customer.name.like(f"%{self.FILTER.get('customer')}%"))

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            self.DATA = pd.DataFrame(dataset, columns=["id", "Tips", "Numurs", "Klients", "Datums",
                                                       "Apm. termiņš", "Apm. datums", "Summa",
                                                       "Valūta", "Prioritāte", "Piezīmes"])
            self.DATA.set_index("id", inplace=True)

        self.endResetModel()



    def flags(self, index):
        return super().flags(index)

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        return False
