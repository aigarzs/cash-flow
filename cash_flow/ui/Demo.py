import pandas as pd
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from cash_flow.database.Model import Customer, Source
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import str_to_priority, pandas_to_python


class Demo(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        filterbox = QHBoxLayout()
        label_filter = QLabel("Filter")
        label_filter.setStyleSheet("font-weight: bold")
        label_customer = QLabel("Customer")
        self.filter_customer = QLineEdit()
        self.filter_customer.editingFinished.connect(self.requery)
        filterbox.addWidget(label_customer)
        filterbox.addWidget(self.filter_customer)
        label_customers_list = QLabel("Customers")
        label_customers_list.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(DemoModel(self.table, self.engine))
        action_add = self.table.context_menu.addAction("Add")
        action_add.triggered.connect(self.action_add)
        action_delete = self.table.context_menu.addAction("Delete")
        action_delete.triggered.connect(self.action_delete)


        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox)
        vbox.addWidget(label_customers_list)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        self.table.model().set_filter({"customer": self.filter_customer.text()})

    def action_add(self):
        row = self.table.selectedIndexes()[0].row()
        self.table.model().insert(row)

    def action_delete(self):
        row = self.table.selectedIndexes()[0].row()
        self.table.model().delete(row)


class DemoModel(ATableModel):
    EMPTY_ROW_AT_BOTTOM = True

    def _do_requery(self):
        stmt = select(Customer.id,
                      Customer.name,
                      Customer.priority,
                      Customer.void) \
            .order_by(Customer.name)

        if self.FILTER.get("customer"):
            stmt = stmt.filter(Customer.name.like(f"%{self.FILTER.get('customer')}%"))

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

        # Convert to DataFrame
        data = pd.DataFrame(dataset, columns=["id", "name", "priority", "void"])
        data.set_index("id", inplace=True)
        return data



    def flags(self, index):
        if index.column() == self.get_column_index("priority"):
            return Qt.ItemFlag.ItemIsEditable | super().flags(index)
        elif index.column() == self.get_column_index("name"):
            return Qt.ItemFlag.ItemIsEditable | super().flags(index)
        elif index.column() == self.get_column_index("void"):
            return Qt.ItemFlag.ItemIsUserCheckable | super().flags(index)
        else:
            return super().flags(index)

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        with Session(self.engine) as session:
            customer = Customer(name="Jauns klients", source_id=Source.DEFAULT, source_key=1, priority=100)
            session.add(customer)
            session.commit()


            return pd.DataFrame([[customer.name, customer.priority, customer.void]],
                            columns=["name", "priority", "void"],
                            index=[customer.id])

    def _cast_input_to_value(self, index, value_str: str):
        if index.column() == self.get_column_index("priority"):
            return str_to_priority(value_str)
        elif index.column() == self.get_column_index("void"):
            return value_str.lower() == "true"
        else:
            return str(value_str)

    def _set_data_in_database(self, index, value):
        """
        You should override this method.
        if self.DATA.index(index.row()) == -1, INSERT new record in database and after update self.DATA.index

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        customer_id = int(self.DATA.index[index.row()])
        stmt_customer = select(Customer).where(Customer.id == customer_id)

        with Session(self.engine) as session:
            customer = session.scalars(stmt_customer).first()

            # Updating current value set (not visible yet in self.DATA)
            if index.column() == self.get_column_index("priority"):
                customer.priority = value
            elif index.column() == self.get_column_index("void"):
                customer.void = value
            elif index.column() == self.get_column_index("name"):
                customer.name = value

            session.commit()

    def _delete_row_in_database(self, row):
        customer_id = int(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(Customer).where(Customer.id == customer_id)
            session.execute(stmt)
            session.commit()