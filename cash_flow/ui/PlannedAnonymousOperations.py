import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QItemDelegate, QComboBox, \
    QStyledItemDelegate, QStackedWidget, QTabWidget
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from cash_flow.database.Model import PlannedAnonymousOperation as Operation
from cash_flow.database.Model import PlannedAnonymousAccount as Account
from cash_flow.database.Model import PlannedAnonymousAmount as Amount
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.ui.ComboAccounts import ComboAccounts
from cash_flow.util.Converters import various_to_integer, str_to_date, various_to_float, various_to_decimal


class PlannedAnonymousOperations(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        label_operations = QLabel("Plānotās anonīmās operācijas")
        label_operations.setStyleSheet("font-weight: bold")

        self.details_stacked = QStackedWidget(self)

        self.table_accounts = AccountsTable(self, self.engine)
        self.table_amounts = AmountsTable(self, self.engine)
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.table_accounts, "Kontējums")
        self.tabs.addTab(self.table_amounts, "Summas")
        self.blank = QWidget(self)
        self.details_stacked.addWidget(self.tabs)
        self.details_stacked.addWidget(self.blank)

        self.table_operations = OperationsTable(self, self.engine)
        self.table_operations.setMaximumHeight(200)

        label_details = QLabel("Detaļas")
        label_details.setStyleSheet("font-weight: bold")

        vbox.addWidget(label_operations)
        vbox.addWidget(self.table_operations)
        vbox.addWidget(label_details)
        vbox.addWidget(self.details_stacked)

        self.setLayout(vbox)

        self.table_operations.model().requery()

    def refresh_details_stacked(self, operation_type: int):
        operation_type = various_to_integer(operation_type)

        if operation_type == 1:
            self.details_stacked.setCurrentWidget(self.tabs)
        else:
            self.details_stacked.setCurrentWidget(self.blank)


class AccountDelegate(QStyledItemDelegate):
    def __init__(self, engine, parent):
        QItemDelegate.__init__(self, parent)
        self.engine = engine

    def createEditor(self, parent, option, index):
        combo = ComboAccounts(self.engine, parent)
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class EntryTypeDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(["DR", "CR"])
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class AmountsModel(ATableModel):
    def set_operation_id(self, id):
        pass

class AmountsTable(ATable):
    def __init__(self, parent, engine):
        super().__init__(parent)

        action_insert = self.context_menu.addAction("Pievienot")
        action_insert.triggered.connect(self.action_insert)
        action_delete = self.context_menu.addAction("Dzēst")
        action_delete.triggered.connect(self.action_delete)

        self.setModel(AmountsModel(self, engine))


    def model(self) -> AmountsModel:
        return super().model()

    def action_insert(self):
        row = self.selectedIndexes()[0].row()
        self.model().insert(row)

    def action_delete(self):
        row = self.selectedIndexes()[0].row()
        self.model().delete(row)


class AmountsModel(ATableModel):
    operation_id = None
    EMPTY_ROW_AT_BOTTOM = True

    def _do_requery(self):
        stmt = select(Amount.id,
                      Amount.date,
                      Amount.amount_LC) \
            .where(Amount.operation_id == self.operation_id)

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            data = pd.DataFrame(dataset, columns=["id", "Datums", "Summa BV"])
            data.set_index("id", inplace=True)
            return data

    def set_operation_id(self, id):
        self.operation_id = various_to_integer(id)
        # print(f"definition_id = {self.definition_id}")
        self.requery()


    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        with Session(self.engine) as session:
            amount = Amount(operation_id=self.operation_id)
            session.add(amount)
            session.commit()

            # Convert to DataFrame
            new_record = pd.DataFrame([[None, None]], columns=["Datums", "Summa BV"], index=[amount.id])

            return new_record

    def _cast_input_to_value(self, index, value_str: str):
        """
        Casts user input on setData to DATABASE compatible value.

        :param index: cell index
        :param value_str: value in string format
        :return: value of correct datatype
        """
        if index.column() == self.get_column_index("Datums"):
            return str_to_date(value_str)
        elif index.column() == self.get_column_index("Summa BV"):
            return various_to_decimal(value_str)
        else:
            return str(value_str)


    def _set_data_in_database(self, index, value):
        """
        Updates DATABASE on setData. You should override this method.

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        amount_id = various_to_integer(self.DATA.index[index.row()])

        with Session(self.engine) as session:
            stmt = select(Amount).where(Amount.id == amount_id)
            amount = session.scalars(stmt).first()

            if self.get_column_index("Datums") == index.column():
                amount.date = value
            elif self.get_column_index("Summa BV") == index.column():
                amount.amount_LC = value

            session.commit()

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        amount_id = various_to_integer(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(Amount).where(Amount.id == amount_id)
            session.execute(stmt)
            session.commit()

class AccountsModel(ATableModel):
    def set_operation_id(self, id):
        pass

class AccountsTable(ATable):
    def __init__(self, parent, engine):
        super().__init__(parent)

        action_insert = self.context_menu.addAction("Pievienot")
        action_insert.triggered.connect(self.action_insert)
        action_delete = self.context_menu.addAction("Dzēst")
        action_delete.triggered.connect(self.action_delete)

        self.entrytype_delegate = EntryTypeDelegate(parent)
        self.account_delegate = AccountDelegate(engine, self)
        self.setModel(AccountsModel(self, engine))
        self.setItemDelegateForColumn(0, self.entrytype_delegate)
        self.setItemDelegateForColumn(1, self.account_delegate)

    def model(self) -> AccountsModel:
        return super().model()

    def action_insert(self):
        row = self.selectedIndexes()[0].row()
        self.model().insert(row)

    def action_delete(self):
        row = self.selectedIndexes()[0].row()
        self.model().delete(row)

class AccountsModel(ATableModel):
    operation_id = None
    EMPTY_ROW_AT_BOTTOM = True

    def _do_requery(self):
        stmt = select(Account.id,
                      Account.entry_type,
                      Account.account,
                      Account.fraction) \
               .order_by(Account.account)

        stmt = stmt.filter(Account.operation_id == self.operation_id)

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            data = pd.DataFrame(dataset, columns=["id", "Tips", "V/G konts", "Frakcija"])
            data.set_index("id", inplace=True)
            return data

    def set_operation_id(self, id):
        self.operation_id = various_to_integer(id)
        # print(f"definition_id = {self.definition_id}")
        self.requery()

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        with Session(self.engine) as session:
            account = Account(operation_id=self.operation_id)
            session.add(account)
            session.commit()

            # Convert to DataFrame
            new_record = pd.DataFrame([[None, None, None]], columns=["Tips", "V/G konts", "Frakcija"], index=[account.id])

            return new_record

    def _cast_input_to_value(self, index, value_str: str):
        """
        Casts user input on setData to DATABASE compatible value.

        :param index: cell index
        :param value_str: value in string format
        :return: value of correct datatype
        """
        if index.column() == self.get_column_index("Tips"):
            return str(value_str)
        elif index.column() == self.get_column_index("V/G konts"):
            return str(value_str)
        elif index.column() == self.get_column_index("Frakcija"):
            return various_to_float(value_str)
        else:
            return str(value_str)

    def _set_data_in_database(self, index, value):
        """
        Updates DATABASE on setData. You should override this method.

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        account_id = various_to_integer(self.DATA.index[index.row()])

        with Session(self.engine) as session:
            stmt = select(Account).where(Account.id == account_id)
            account = session.scalars(stmt).first()

            if self.get_column_index("Tips") == index.column():
                account.entry_type = value
            elif self.get_column_index("V/G konts") == index.column():
                account.account = value
            elif self.get_column_index("Frakcija") == index.column():
                account.fraction = value

            session.commit()

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        account_id = various_to_integer(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(Account).where(Account.id == account_id)
            session.execute(stmt)
            session.commit()


class OperationsTable(ATable):
    def __init__(self, parent: PlannedAnonymousOperations, engine):
        super().__init__(parent)
        action_insert = self.context_menu.addAction("Pievienot")
        action_insert.triggered.connect(self.action_insert)
        action_delete = self.context_menu.addAction("Dzēst")
        action_delete.triggered.connect(self.action_delete)

        self.setModel(OperationsModel(self, engine))
        self.selectionModel().currentRowChanged.connect(self.row_changed)

    def parent(self) -> PlannedAnonymousOperations:
        return super().parent()

    def row_changed(self, index_current, index_previous):
        try:
            operation_id = self.model().DATA.index[index_current.row()]
            operation_type = 1
        except IndexError as err:
            operation_id = None
            operation_type = 0

        self.parent().table_accounts.model().set_operation_id(operation_id)
        self.parent().table_amounts.model().set_operation_id(operation_id)

        self.parent().refresh_details_stacked(operation_type)

    def action_insert(self):
        row = self.selectedIndexes()[0].row()
        self.model().insert(row)

    def action_delete(self):
        row = self.selectedIndexes()[0].row()
        self.model().delete(row)


class OperationsModel(ATableModel):

    EMPTY_ROW_AT_BOTTOM = True

    def parent(self) -> OperationsTable:
        return super().parent()

    def _do_requery(self):
        stmt = select(Operation.id,
                      Operation.name) \
               .order_by(Operation.name)

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            data = pd.DataFrame(dataset, columns=["id", "Nosaukums"])
            data.set_index("id", inplace=True)

        self.parent().parent().refresh_details_stacked(0)
        return data


    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        with Session(self.engine) as session:
            operation = Operation()
            session.add(operation)
            session.commit()

            # Convert to DataFrame
            new_record = pd.DataFrame([[None]], columns=["Nosaukums"], index=[operation.id])

            return new_record

    def _cast_input_to_value(self, index, value_str: str):
        """
        Casts user input on setData to DATABASE compatible value.

        :param index: cell index
        :param value_str: value in string format
        :return: value of correct datatype
        """
        return str(value_str)

    def _set_data_in_database(self, index, value):
        """
        Updates DATABASE on setData. You should override this method.

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        operation_id = various_to_integer(self.DATA.index[index.row()])

        with Session(self.engine) as session:
            stmt = select(Operation).where(Operation.id == operation_id)
            operation = session.scalars(stmt).first()

            if self.get_column_index("Nosaukums") == index.column():
                operation.name = value

            session.commit()

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        operation_id = various_to_integer(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(Operation).where(Operation.id == operation_id)
            session.execute(stmt)
            session.commit()
