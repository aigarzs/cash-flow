import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu, QItemDelegate, QComboBox, \
    QStyledItemDelegate, QStackedWidget
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from cash_flow.database.Model import CashFlowDefinition as CFDefinition
from cash_flow.database.Model import CashFlowDefinitionAccount as CFAccount
from cash_flow.database.Model import CashFlowDefinitionTotal as CFTotal
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.ui.ComboAccounts import ComboAccounts
from cash_flow.ui.ComboDefinition import ComboDefinition
from cash_flow.util.Converters import various_to_integer


class CashFlowDefinition(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        label_definition = QLabel("Naudas plūsmas struktūra")
        label_definition.setStyleSheet("font-weight: bold")

        self.details_stacked = QStackedWidget(self)
        self.details_stacked.setMaximumHeight(200)

        self.table_accounts = AccountsTable(self, self.engine)
        self.table_totals = TotalsTable(self, self.engine)
        self.blank = QWidget(self)
        self.details_stacked.addWidget(self.table_accounts)
        self.details_stacked.addWidget(self.table_totals)
        self.details_stacked.addWidget(self.blank)

        self.table_structure = StructureTable(self, self.engine)

        label_details = QLabel("Detaļas")
        label_details.setStyleSheet("font-weight: bold")

        vbox.addWidget(label_definition)
        vbox.addWidget(self.table_structure)
        vbox.addWidget(label_details)
        vbox.addWidget(self.details_stacked)

        self.setLayout(vbox)

        self.table_structure.model().requery()

    def refresh_details_stacked(self, definition_type: int):
        definition_type = various_to_integer(definition_type)

        if definition_type == 1:
            self.details_stacked.setCurrentWidget(self.table_accounts)
        elif definition_type == 2:
            self.details_stacked.setCurrentWidget(self.table_totals)
        else:
            self.details_stacked.setCurrentWidget(self.blank)


class DefinitionTypeDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(StructureModel.TYPE_DICT.values())
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class StructureDelegate(QStyledItemDelegate):
    def __init__(self, engine, parent):
        QItemDelegate.__init__(self, parent)
        self.engine = engine

    def createEditor(self, parent, option, index):
        combo = ComboDefinition(self.engine, parent)
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class AccountDelegate(QStyledItemDelegate):
    def __init__(self, engine, parent):
        QItemDelegate.__init__(self, parent)
        self.engine = engine

    def createEditor(self, parent, option, index):
        combo = ComboAccounts(self.engine, parent)
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class CashTypeDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(AccountsModel.TYPE_DICT.values())
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class TotalsModel(ATableModel):
    def set_definition_id(self, id):
        pass

class TotalsTable(ATable):
    def __init__(self, parent, engine):
        super().__init__(parent)

        action_insert = self.context_menu.addAction("Pievienot")
        action_insert.triggered.connect(self.action_insert)
        action_delete = self.context_menu.addAction("Dzēst")
        action_delete.triggered.connect(self.action_delete)

        self.setModel(TotalsModel(self, engine))

        self.structure_delegate = StructureDelegate(engine, self)
        self.setItemDelegateForColumn(0, self.structure_delegate)

    def model(self) -> TotalsModel:
        return super().model()

    def action_insert(self):
        row = self.selectedIndexes()[0].row()
        self.model().insert(row)

    def action_delete(self):
        row = self.selectedIndexes()[0].row()
        self.model().delete(row)


class TotalsModel(ATableModel):
    definition_id = None
    EMPTY_ROW_AT_BOTTOM = True

    def _do_requery(self):
        stmt = select(CFTotal.id,
                      CFDefinition.name) \
            .join(CFDefinition, CFTotal.definition_summarized==CFDefinition.id) \
            .filter(CFTotal.definition_id == self.definition_id)

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            data = pd.DataFrame(dataset, columns=["id", "Kopsummas"])
            data.set_index("id", inplace=True)
            return data

    def set_definition_id(self, id):
        self.definition_id = various_to_integer(id)
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
            totals = CFTotal(definition_id=self.definition_id)
            session.add(totals)
            session.commit()

            # Convert to DataFrame
            new_record = pd.DataFrame([[None]], columns=["Kopsummas"], index=[totals.id])

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
        totals_id = various_to_integer(self.DATA.index[index.row()])

        with Session(self.engine) as session:
            stmt = select(CFTotal).where(CFTotal.id == totals_id)
            totals = session.scalars(stmt).first()

            if self.get_column_index("Kopsummas") == index.column():
                s = select(CFDefinition).where(CFDefinition.name == value)
                t = session.scalars(s).first()
                totals.definition_summarized = t.id

            session.commit()

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        totals_id = various_to_integer(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(CFTotal).where(CFTotal.id == totals_id)
            session.execute(stmt)
            session.commit()

class AccountsModel(ATableModel):
    def set_definition_id(self, id):
        pass

class AccountsTable(ATable):
    def __init__(self, parent, engine):
        super().__init__(parent)

        action_insert = self.context_menu.addAction("Pievienot")
        action_insert.triggered.connect(self.action_insert)
        action_delete = self.context_menu.addAction("Dzēst")
        action_delete.triggered.connect(self.action_delete)

        self.cashtype_delegate = CashTypeDelegate(self)
        self.account_delegate = AccountDelegate(engine, self)
        self.setModel(AccountsModel(self, engine))
        self.setItemDelegateForColumn(0, self.cashtype_delegate)
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
    definition_id = None
    EMPTY_ROW_AT_BOTTOM = True
    TYPE_DICT = {"Receipt": "Ieņēmumi", "Payment": "Maksājumi"}

    def _do_requery(self):
        stmt = select(CFAccount.id,
                      CFAccount.cash_type,
                      CFAccount.account) \
               .order_by(CFAccount.account)

        stmt = stmt.filter(CFAccount.definition_id == self.definition_id)

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            data = pd.DataFrame(dataset, columns=["id", "Tips", "V/G konts"])
            data.set_index("id", inplace=True)
            return data

    def set_definition_id(self, id):
        self.definition_id = various_to_integer(id)
        # print(f"definition_id = {self.definition_id}")
        self.requery()

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def _get_value(self, index):
        try:
            value = self.DATA.iloc[index.row(), index.column()]
            if index.column() == self.get_column_index("Tips"): value = self.TYPE_DICT.get(value)
        except IndexError as err:
            value = None

        return value

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        with Session(self.engine) as session:
            accounts = CFAccount(definition_id=self.definition_id)
            session.add(accounts)
            session.commit()

            # Convert to DataFrame
            new_record = pd.DataFrame([[None, None]], columns=["Tips", "V/G konts"], index=[accounts.id])

            return new_record

    def _cast_input_to_value(self, index, value_str: str):
        """
        Casts user input on setData to DATABASE compatible value.

        :param index: cell index
        :param value_str: value in string format
        :return: value of correct datatype
        """
        if self.get_column_index("Tips") == index.column():
            reversed_types = {v: k for k, v in self.TYPE_DICT.items()}
            value = reversed_types[value_str]
            return value
        else:
            return str(value_str)

    def _set_data_in_database(self, index, value):
        """
        Updates DATABASE on setData. You should override this method.

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        accounts_id = various_to_integer(self.DATA.index[index.row()])

        with Session(self.engine) as session:
            stmt = select(CFAccount).where(CFAccount.id == accounts_id)
            accounts = session.scalars(stmt).first()

            if self.get_column_index("Tips") == index.column():
                accounts.cash_type = value
            elif self.get_column_index("V/G konts") == index.column():
                accounts.account = value

            session.commit()

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        accounts_id = various_to_integer(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(CFAccount).where(CFAccount.id == accounts_id)
            session.execute(stmt)
            session.commit()


class StructureTable(ATable):
    def __init__(self, parent: CashFlowDefinition, engine):
        super().__init__(parent)
        action_insert = self.context_menu.addAction("Pievienot")
        action_insert.triggered.connect(self.action_insert)
        action_delete = self.context_menu.addAction("Dzēst")
        action_delete.triggered.connect(self.action_delete)

        self.setModel(StructureModel(self, engine))
        self.type_delegate = DefinitionTypeDelegate(self)
        self.setItemDelegateForColumn(1, self.type_delegate)
        self.selectionModel().currentRowChanged.connect(self.row_changed)

    def parent(self) -> CashFlowDefinition:
        return super().parent()

    def row_changed(self, index_current, index_previous):
        try:
            definition_id = self.model().DATA.index[index_current.row()]
            definition_type = self.model().DATA.iloc[index_current.row(), 1]
        except IndexError as err:
            definition_id = None
            definition_type = None

        self.parent().table_accounts.model().set_definition_id(definition_id)
        self.parent().table_totals.model().set_definition_id(definition_id)

        self.parent().refresh_details_stacked(definition_type)

    def action_insert(self):
        row = self.selectedIndexes()[0].row()
        self.model().insert(row)

    def action_delete(self):
        row = self.selectedIndexes()[0].row()
        self.model().delete(row)


class StructureModel(ATableModel):

    EMPTY_ROW_AT_BOTTOM = True

    TYPE_DICT = {None: "", 1: "Kontu grafiks", 2: "Kopsummas", 3: "Bilance"}

    def parent(self) -> StructureTable:
        return super().parent()

    def _do_requery(self):
        stmt = select(CFDefinition.id,
                      CFDefinition.key,
                      CFDefinition.definition_type,
                      CFDefinition.name) \
               .order_by(CFDefinition.key)

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            data = pd.DataFrame(dataset, columns=["id", "Nr.", "Tips", "Nosaukums"])
            data.set_index("id", inplace=True)

        self.parent().parent().refresh_details_stacked(0)
        return data


    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def _get_value(self, index):
        try:
            value = self.DATA.iloc[index.row(), index.column()]
            if index.column() == self.get_column_index("Tips"): value = self.TYPE_DICT.get(value)
        except IndexError as err:
            value = None

        return value

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        with Session(self.engine) as session:
            definition = CFDefinition()
            session.add(definition)
            session.commit()

            # Convert to DataFrame
            new_record = pd.DataFrame([[None, np.nan, None]], columns=["Nr.", "Tips", "Nosaukums"], index=[definition.id])

            return new_record

    def _cast_input_to_value(self, index, value_str: str):
        """
        Casts user input on setData to DATABASE compatible value.

        :param index: cell index
        :param value_str: value in string format
        :return: value of correct datatype
        """
        if self.get_column_index("Tips") == index.column():
            reversed_types = {v: k for k, v in self.TYPE_DICT.items()}
            value = reversed_types[value_str]
            return value
        else:
            return str(value_str)

    def _set_data_in_database(self, index, value):
        """
        Updates DATABASE on setData. You should override this method.

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        definition_id = various_to_integer(self.DATA.index[index.row()])

        with Session(self.engine) as session:
            stmt = select(CFDefinition).where(CFDefinition.id == definition_id)
            definition = session.scalars(stmt).first()

            if self.get_column_index("Nr.") == index.column():
                definition.key = value
            elif self.get_column_index("Nosaukums") == index.column():
                definition.name = value
            elif self.get_column_index("Tips") == index.column():
                definition.definition_type = value
                self.parent().parent().refresh_details_stacked(value)

            session.commit()

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        definition_id = various_to_integer(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(CFDefinition).where(CFDefinition.id == definition_id)
            session.execute(stmt)
            session.commit()
