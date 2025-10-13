import inspect
import sys
import threading
from datetime import date, datetime
from decimal import Decimal
from pandas._libs.tslibs.timestamps import Timestamp
import pandas.api.types as ptypes

import numpy as np
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, QMetaObject, QObject, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QTableView, QHeaderView, QMenu
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from cash_flow.util.Converters import decimal_format, date_format, str_to_date, pandas_to_python
import pandas as pd

from cash_flow.util.gui import stylesheet_table_headers
from cash_flow.util.log import get_logger


class ATableModel:
    def requery(self):
        pass


class ATable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # This header formatting is required on Windows. On Linux model().headerData() works fine
        self.horizontalHeader().setStyleSheet(stylesheet_table_headers())
        self.verticalHeader().setStyleSheet(stylesheet_table_headers())

        self.context_menu = QMenu()
        action_requery = self.context_menu.addAction("Pārrēķināt")
        action_requery.triggered.connect(self.action_requery)

    def setModel(self, model: ATableModel):
        super().setModel(model)
        #for i in range(model.columnCount()):
        #    self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def model(self) -> ATableModel:
        return super().model()

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())

    def action_requery(self):
        self.model().requery()

class ATableModel(QAbstractTableModel):
    # Populated by requery(), updated by setData
    DATA = pd.DataFrame()
    # Optional way of formatting.
    # You may get flags() and / or _format_background() from data in self.FORMAT
    FORMAT = pd.DataFrame()
    # Free format library, set by set_filter(...), used by _do_requery()
    FILTER = {}

    EMPTY_ROW_AT_BOTTOM = False

    lock = threading.Lock()

    def __init__(self, table: ATable, engine: Engine):
        super().__init__(table)
        self.engine = engine
        self.logger = get_logger(self)
        # This causes ATable to requery twice, since I do requery after gui is built
        # self.requery()

    def _do_requery(self):
        """
        Generate DataFrame from DATABASE

        :return: DataFrame
        """
        raise Exception(self.__class__.__name__ + ":" + inspect.currentframe().f_code.co_name +
                        ". You should override this method")


    def _get_value(self, index):
        """
        This retrieves value from self.DATA and converts to user-friendly format.
        You should override this method for combos etc.

        :param index: index of cell
        :return: user-friendly value
        """
        try:
            with self.lock:
                val = self.DATA.iloc[index.row(), index.column()]
            value = pandas_to_python(val)
        except IndexError as err:
            value = None
        except Exception as err:
            self.logger.error(err)
            value = None

        return value

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        raise Exception(self.__class__.__name__ + ":" + inspect.currentframe().f_code.co_name +
                        ". You should override this method")

    def _cast_input_to_value(self, index, value_str: str):
        """
        Casts user input on setData to DATABASE compatible value.

        :param index: cell index
        :param value_str: value in string format
        :return: value of correct datatype
        """
        raise Exception(self.__class__.__name__ + ":" + inspect.currentframe().f_code.co_name +
                        ". You should override this method")

    def _set_data_in_database(self, index, value):
        """
        Updates DATABASE on setData. You should override this method.

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        raise Exception(self.__class__.__name__ + ":" + inspect.currentframe().f_code.co_name +
                        ". You should override this method")

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        raise Exception(self.__class__.__name__ + ":" + inspect.currentframe().f_code.co_name +
                        ". You should override this method")

    def parent(self) -> ATable:
        return super().parent()

    def get_column_index(self, column_name: str):
        with self.lock:
            data_columns = self.DATA.columns.tolist()

        for i in range(self.columnCount()):
            if data_columns[i] == column_name:
                    return i

        return None

    def get_column_name(self, column_index):
        with self.lock:
            try:
                return self.DATA.columns[column_index]
            except IndexError as err:
                return None

    def set_filter(self, filter):
        with self.lock:
            self.FILTER = filter
            self.logger.debug(f"Filter: {self.FILTER}")
        self.requery()

    def requery(self):
        self.thread = QThread()
        self.worker = RequeryWorker(self)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_requery_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.logger.debug(f"Requery start")

        self.thread.start()




    @pyqtSlot(pd.DataFrame)
    def on_requery_finished(self, df):
        self.logger.debug(f"_on_requery completed")
        self.beginResetModel()

        with self.lock:
            self.DATA = df
            # self.logger.debug("Data types:\n", self.DATA.dtypes)
            # self.logger.debug(f"Shape: {self.DATA.shape}")
            # self.logger.debug(f"Columns: {self.DATA.columns}")
            # self.logger.debug("Data:\n", self.DATA.head())
            shape = self.DATA.shape

        self.endResetModel()
        self.logger.info(f"Requery finished. Shape: {shape}")


    def rowCount(self, parent=None):
        empty_row_count = 1 if self.EMPTY_ROW_AT_BOTTOM else 0
        with self.lock:
            row_count = self.DATA.shape[0] + empty_row_count
        # self.logger.debug(f"rowCount: {row_count}")
        return row_count

    def columnCount(self, parent=None):
        with self.lock:
            column_count = self.DATA.shape[1]
        # self.logger.debug(f"columnCount: {column_count}")
        return column_count

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        # self.logger.debug(f"headerData section-{section} orientation-{orientation}")
        header = None

        if role == Qt.ItemDataRole.DisplayRole:
            with self.lock:
                data_columns = self.DATA.columns.tolist()
                data_index = self.DATA.index

            try:
                if orientation == Qt.Orientation.Horizontal:
                    header = str(data_columns[section])
                elif orientation == Qt.Orientation.Vertical:
                    header = str(data_index[section])
            except IndexError as err:
                # For example index for new record row
                header = None
            except Exception as err:
                self.logger.error(err)
                header = None

        # self.logger.debug(f"headerData section-{section} orientation-{orientation} : {header}")
        return header

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # self.logger.debug(f"data @ {(index.row(), index.column())} , Role {str(role)}")

        if not index.isValid():
            value = None

        elif role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole,
                    Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.TextAlignmentRole):
            value = self._get_value(index)
            value = self._format_value(value, role)

        elif role == Qt.ItemDataRole.BackgroundRole:
            value = self._format_background(index, role)

        else:
            value = None

        # self.logger.debug(f"data @ {(index.row(), index.column())} , Role {str(role)}: {value}")
        return value

    def _format_value(self, value, role=Qt.ItemDataRole.DisplayRole):
        """
        This applies formatting based on value

        :param value: value from self.DATA
        :param role: Qt.ItemDataRole
        :return: formatted value
        """
        if role == Qt.ItemDataRole.DisplayRole:
            # print(type(value) , " " , value)
            if value is None:
                return ""
            elif type(value) in (Decimal, float):
                return decimal_format().format(value)
            elif type(value) in (date, datetime):
                return value.strftime(date_format())
            elif type(value) == bool:
                return None
            else:
                return str(value)

        elif role == Qt.ItemDataRole.CheckStateRole:
            if type(value) == bool:
                return Qt.CheckState.Checked if value else Qt.CheckState.Unchecked

        elif role == Qt.ItemDataRole.EditRole:
            if type(value) == Decimal:
                return decimal_format().format(value)
            elif value is None:
                return ""
            else:
                return str(value)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if type(value) in (Decimal, float, int):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def _format_background(self, index, role=Qt.ItemDataRole.BackgroundRole):
        """
        This formats cell background.
        Default implementation is based on self.flags() - Qt.ItemFlag.ItemIsEditable
        You can implement this method based on self.FORMAT

        :param index: index of cell
        :param role: Qt.ItemDataRole.BackgroundRole
        :return: QBrush - cell background
        """
        # self.logger.debug(f"cell background {(index.row(), index.column())}")
        background = None

        flags = self.flags(index)

        if role == Qt.ItemDataRole.BackgroundRole:
            if Qt.ItemFlag.ItemIsEditable in flags \
                    or Qt.ItemFlag.ItemIsUserCheckable in flags:
                # This is very dark color, good for dark theme
                # return QBrush(Qt.GlobalColor.color1)
                # This is light color, good for light theme
                background = QBrush(QColor("#edf4f7"))

        # self.logger.debug(f"cell background {(index.row(), index.column())} : {background}")
        return background

    def flags(self, index):
        """
        Do not override this method.
        This method is failsafe,
        Implement _get_flags(index) instead.
        If this method fails, GUI crashed
        :param index: item index
        :return: flags

        """

        try:
            flags = self._get_flags(index)
        except Exception as err:
            self.logger.error(f"Flags error: {err}")
            flags = QAbstractTableModel.flags(self, index)

        return flags

    def _get_flags(self, index):
        """"
        Override this method to get flags based on index.
        """
        """
        return QAbstractTableModel.flags(self, index) | Qt.ItemFlag.ItemIsEditable
        """

        return QAbstractTableModel.flags(self, index)

    def insert(self, row):
        # row + 1 for that cursor stays on new row
        self.beginInsertRows(QModelIndex(), row+1, row+1)
        new_row = self._generate_default_row()

        # Concatenate the DataFrames
        with self.lock:
            self.DATA = pd.concat([self.DATA[:row], new_row, self.DATA[row:]])

        self.endInsertRows()

    def delete(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self._delete_row_in_database(row)

        with self.lock:
            self.DATA = pd.concat([self.DATA[:row], self.DATA[row + 1:]])

        self.endRemoveRows()

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role == Qt.ItemDataRole.CheckStateRole:
            checked = value == 2  # Qt.CheckState.Checked
            value = "true" if checked else "false"
            role = Qt.ItemDataRole.EditRole

        if role == Qt.ItemDataRole.EditRole:
            try:
                value = self._cast_input_to_value(index, value)
                # print("Accepted value: " + str(value))
                with self.lock:
                    data_index = self.DATA.index

                if index.row() >= len(data_index):
                    self.insert(index.row())
                self._set_data_in_database(index, value)
                # print("Set value in database")
                with self.lock:
                    self.DATA.iloc[index.row(), index.column()] = value
                # print("Updated DATA")
                self.parent().resizeColumnToContents(index.column())
                return True
            except Exception as err:
                print(self.__class__.__name__ + ":" + inspect.currentframe().f_code.co_name + ": " + str(err))
                # raise err
                return False

        return False


class RequeryWorker(QObject):
    finished = pyqtSignal(pd.DataFrame)

    def __init__(self, model: ATableModel):
        super().__init__()
        self.model = model
        self.logger = get_logger(model)

    def run(self):
        self.logger.debug(f"RequeryWorker started")
        try:
            df = self.model._do_requery()
            if df is None:
                df = pd.DataFrame({})
        except Exception as err:
            self.logger.error(f"RequeryWorker error: {err}")
            df = pd.DataFrame({})
        self.logger.debug(f"RequeryWorker finished")
        self.finished.emit(df)
