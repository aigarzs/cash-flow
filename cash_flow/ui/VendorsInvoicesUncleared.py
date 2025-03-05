from datetime import date, datetime

import pandas as pd
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Document, DocType, Vendor
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import str_to_date, str_to_priority


class VendorsInvoicesUncleared(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        filterbox = QHBoxLayout()
        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")
        label_vendor = QLabel("Piegādātājs")
        self.filter_vendor = QLineEdit()
        self.filter_vendor.editingFinished.connect(self.requery)
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
        filterbox.addWidget(label_vendor)
        filterbox.addWidget(self.filter_vendor)
        filterbox.addWidget(label_date_planned)
        filterbox.addWidget(self.filter_date_from)
        filterbox.addWidget(self.filter_date_through)
        label_invoices = QLabel("Rēķini")
        label_invoices.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(VendorsInvoicesUnclearedModel(self.table, self.engine))
        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox)
        vbox.addWidget(label_invoices)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        self.table.model().set_filter({"date from": self.filter_date_from.date().toPyDate(),
                                       "date through": self.filter_date_through.date().toPyDate(),
                                       "vendor": self.filter_vendor.text()})


class VendorsInvoicesUnclearedModel(ATableModel):

    def requery(self):
        self.beginResetModel()

        stmt = select(Document.id,
                      DocType.name,
                      Document.number,
                      Vendor.name,
                      Document.date,
                      Document.date_due,
                      Document.date_planned_clearing,
                      Document.amount,
                      Document.amount - Document.cleared_amount,
                      Document.currency,
                      Document.priority,
                      Document.void,
                      Document.memo) \
            .join(DocType) \
            .join(Vendor) \
            .where(Document.type_id.in_([DocType.INVOICE_VENDOR, DocType.PAYROLL]),
                   Document.cleared == False) \
            .order_by(Document.date_planned_clearing, Vendor.name, Document.priority, Document.date_due, Document.id)

        if self.FILTER.get("date from"):
            stmt = stmt.filter(Document.date_planned_clearing >= self.FILTER.get("date from"))
        if self.FILTER.get("date through"):
            stmt = stmt.filter(Document.date_planned_clearing <= self.FILTER.get("date through"))
        if self.FILTER.get("vendor"):
            stmt = stmt.filter(Vendor.name.like(f"%{self.FILTER.get('vendor')}%"))

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            self.DATA = pd.DataFrame(dataset, columns=["id", "Tips", "Numurs", "Piegādātājs",
                                                       "Datums", "Apm.termiņš", "Plānotais datums", "Summa", "Atlikusī summa",
                                                       "Valūta", "Prioritāte", "Anulēts", "Piezīmes"])
            self.DATA.set_index("id", inplace=True)

        self.endResetModel()


    def flags(self, index):
        if index.column() == self.get_column_index("Piezīmes") or \
                index.column() == self.get_column_index("Plānotais datums") or \
                index.column() == self.get_column_index("Prioritāte"):
            return Qt.ItemFlag.ItemIsEditable | super().flags(index)
        elif index.column() == self.get_column_index("Anulēts"):
            return Qt.ItemFlag.ItemIsUserCheckable | super().flags(index)
        else:
            return super().flags(index)

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        # save value from editor to member DATA
        doc_id = int(self.DATA.index[index.row()])
        stmt_doc = select(Document).where(Document.id == doc_id)

        if role == Qt.ItemDataRole.EditRole or role == Qt.ItemDataRole.CheckStateRole:
            with Session(self.engine) as session:
                doc = session.scalars(stmt_doc).first()
                if index.column() == self.get_column_index("Piezīmes"):
                    doc.memo = value
                elif index.column() == self.get_column_index("Plānotais datums"):
                    value = str_to_date(value)
                    doc.date_planned_clearing = value
                elif index.column() == self.get_column_index("Prioritāte"):
                    value = str_to_priority(value)
                    doc.priority = value
                elif index.column() == self.get_column_index("Anulēts"):
                    checked = value == 2  # Qt.CheckState.Checked
                    value = checked
                    doc.void = value
                session.commit()
            self.DATA.iloc[index.row(), index.column()] = value
            self.parent().resizeColumnToContents(index.column())
            return True
        return False
