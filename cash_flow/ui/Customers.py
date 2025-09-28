import pandas as pd
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel
from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Partner
# from cash_flow.database.Model import Customer
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import str_to_priority


class Customers(QWidget):
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
        filterbox.addWidget(label_customer)
        filterbox.addWidget(self.filter_customer)
        label_customers_list = QLabel("Klienti")
        label_customers_list.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(CustomersModel(self.table, self.engine))

        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox)
        vbox.addWidget(label_customers_list)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        self.table.model().set_filter({"customer": self.filter_customer.text()})


class CustomersModel(ATableModel):

    def _do_requery(self):

        stmt = select(Partner.id,
                      Partner.name,
                      Partner.dr_priority,
                      Partner.dr_void) \
            .order_by(Partner.name)

        if self.FILTER.get("customer"):
            stmt = stmt.filter(Partner.name.like(f"%{self.FILTER.get('customer')}%"))

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            df = pd.DataFrame(dataset, columns=["id", "Nosaukums", "Prioritāte", "Anulēt"])
            df.set_index("id", inplace=True)
            return df



    def flags(self, index):
        if index.column() == self.get_column_index("Prioritāte"):
            return Qt.ItemFlag.ItemIsEditable | super().flags(index)
        elif index.column() == self.get_column_index("Anulēt"):
            return Qt.ItemFlag.ItemIsUserCheckable | super().flags(index)
        else:
            return super().flags(index)

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        # save value from editor to member DATA
        customer_id = int(self.DATA.index[index.row()])
        stmt_customer = select(Partner).where(Partner.id == customer_id)

        if role == Qt.ItemDataRole.EditRole or role == Qt.ItemDataRole.CheckStateRole:
            with Session(self.engine) as session:
                customer = session.scalars(stmt_customer).first()
                if index.column() == self.get_column_index("Prioritāte"):
                    value = str_to_priority(value)
                    customer.dr_priority = value
                    session.commit()
                    self.DATA.iloc[index.row(), index.column()] = value
                    return True
                elif index.column() == self.get_column_index("Anulēt"):
                    checked = value == 2  # Qt.CheckState.Checked
                    customer.dr_void = checked
                    session.commit()
                    self.DATA.iloc[index.row(), index.column()] = checked
                    return True

        return False
