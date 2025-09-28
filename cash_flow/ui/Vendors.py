from datetime import date, datetime

import pandas as pd
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Partner
# from cash_flow.database.Model import Vendor
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import str_to_priority


class Vendors(QWidget):
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
        filterbox.addWidget(label_vendor)
        filterbox.addWidget(self.filter_vendor)
        label_vendors_list = QLabel("Piegādātāji")
        label_vendors_list.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(VendorsModel(self.table, self.engine))

        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox)
        vbox.addWidget(label_vendors_list)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        self.table.model().set_filter({"vendor": self.filter_vendor.text()})


class VendorsModel(ATableModel):

    def _do_requery(self):

        stmt = select(Partner.id,
                      Partner.name,
                      Partner.cr_priority,
                      Partner.cr_void) \
                .order_by(Partner.name)

        if self.FILTER.get("vendor"):
            stmt = stmt.filter(Partner.name.like(f"%{self.FILTER.get('vendor')}%"))

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            df = pd.DataFrame(dataset, columns=["id", "Nosaukums", "Prioritāte", "Anulēts"])
            df.set_index("id", inplace=True)
            return df




    def flags(self, index):
        if index.column() == self.get_column_index("Prioritāte"):
            return Qt.ItemFlag.ItemIsEditable | super().flags(index)
        elif index.column() == self.get_column_index("Anulēts"):
            return Qt.ItemFlag.ItemIsUserCheckable | super().flags(index)
        else:
            return super().flags(index)

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        # save value from editor to member DATA
        vendor_id = int(self.DATA.index[index.row()])
        stmt_vendor = select(Partner).where(Partner.id == vendor_id)

        if role == Qt.ItemDataRole.EditRole or role == Qt.ItemDataRole.CheckStateRole:
            with Session(self.engine) as session:
                vendor = session.scalars(stmt_vendor).first()
                if index.column() == self.get_column_index("Prioritāte"):
                    value = str_to_priority(value)
                    vendor.cr_priority = value
                    session.commit()
                    self.DATA.iloc[index.row(), index.column()] = value
                    return True
                elif index.column() == self.get_column_index("Anulēts"):
                    checked = value == 2  # Qt.CheckState.Checked
                    vendor.cr_void = checked
                    session.commit()
                    self.DATA.iloc[index.row(), index.column()] = checked
                    return True

        return False
