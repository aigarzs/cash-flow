from datetime import date, datetime

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLineEdit, QLabel, QAbstractItemView, \
    QPushButton, QStackedWidget, QComboBox, QStyledItemDelegate, QItemDelegate
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from cash_flow.database.Model import BudgetEntry
from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import various_to_integer, various_to_decimal, str_to_date, date_format


class Budget(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        vbox = QVBoxLayout()
        self.stacked_widget = QStackedWidget()
        self.budget_view = BudgetView(engine, self)
        self.details_view = DetailsView(engine, self)
        self.stacked_widget.addWidget(self.budget_view)
        self.stacked_widget.addWidget(self.details_view)
        vbox.addWidget(self.stacked_widget)
        self.setLayout(vbox)

    def refresh_view(self, index):
        self.stacked_widget.setCurrentIndex(index if index == 1 else 0)


class BudgetView(QWidget):
    def __init__(self, engine, main_view: Budget):
        super().__init__(main_view)
        self.engine = engine
        self.main_view = main_view
        vbox = QVBoxLayout()
        filterbox_from = QHBoxLayout()
        filterbox_through = QHBoxLayout()
        filterbox_freq = QHBoxLayout()
        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")
        label_dateFrom = QLabel("No datuma")
        self.filter_dateFrom = QDateEdit()
        self.filter_dateFrom.setCalendarPopup(True)
        self.filter_dateFrom.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_dateFrom.setDate(datetime.now())
        self.filter_dateFrom.dateChanged.connect(self.requery)
        filterbox_from.addWidget(label_dateFrom)
        filterbox_from.addWidget(self.filter_dateFrom)
        label_dateThrough = QLabel("Līdz datumam")
        self.filter_dateThrough = QDateEdit()
        self.filter_dateThrough.setCalendarPopup(True)
        self.filter_dateThrough.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_dateThrough.setDate(date(datetime.now().year, 12, 31))
        self.filter_dateThrough.dateChanged.connect(self.requery)
        filterbox_through.addWidget(label_dateThrough)
        filterbox_through.addWidget(self.filter_dateThrough)
        label_freq = QLabel("Periodiskums")
        self.filter_Frequency = QComboBox(self)
        self.filter_Frequency.addItems(frequency_map.keys())
        self.filter_Frequency.setCurrentText("Mēnesis")
        self.filter_Frequency.currentIndexChanged.connect(self.requery)
        filterbox_freq.addWidget(label_freq)
        filterbox_freq.addWidget(self.filter_Frequency)
        toolsbox = QHBoxLayout()
        btn_edit = QPushButton("Labot")
        btn_edit.clicked.connect(self.edit_budget)
        toolsbox.addStretch()
        toolsbox.addWidget(btn_edit)
        label_CFStructure = QLabel("Naudas Plūsmas Budžets")
        label_CFStructure.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(BudgetViewModel(self.table, self.engine))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.selectionModel().currentRowChanged.connect(self.row_changed)

        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox_from)
        vbox.addLayout(filterbox_through)
        vbox.addLayout(filterbox_freq)
        vbox.addLayout(toolsbox)
        vbox.addWidget(label_CFStructure)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        selected_freq = self.filter_Frequency.currentText()
        freq = frequency_map[selected_freq]
        self.table.model().set_filter({"date from": self.filter_dateFrom.date().startOfDay().toPyDateTime(),
                                       "date through": self.filter_dateThrough.date().endOfDay().toPyDateTime(),
                                       "frequency": freq})

    def edit_budget(self):
        self.main_view.refresh_view(1)
        self.main_view.details_view.clear_commandsbox()
        self.main_view.details_view.requery()

    def row_changed(self, index_current, index_previous):
        try:
            definition_id = self.table.model().DATA.index[index_current.row()]
            name = self.table.model().DATA.iloc[index_current.row(), 0]
        except IndexError as err:
            definition_id = None
            name = None

        self.main_view.details_view.field_name.setText(name)
        self.main_view.details_view.table.model().set_definition_id(definition_id)

class BudgetViewModel(ATableModel):

    def _do_requery(self):
        # Setup filters
        date_from = str(self.FILTER.get("date from"))
        date_through = str(self.FILTER.get("date through"))
        report_period = self.FILTER.get("frequency")

        sql = "SELECT * FROM F01_BudgetEntries WHERE date >= '" + date_from + "' AND date <= '" + date_through + "'"
        # print(sql)
        budget_entries_df = pd.read_sql_query(
            sql,
            self.engine)
        definition_df = pd.read_sql_query("SELECT * FROM E01_CashFlowDefinition WHERE definition_type = 1", self.engine)

        budget_entries_df["date"] = pd.to_datetime(budget_entries_df['date'])
        offset = offset_map.get(report_period, pd.offsets.MonthEnd(0))
        budget_entries_df["period"] = pd.to_datetime(budget_entries_df["date"], format="mixed", errors="coerce").apply(
            lambda d: offset.rollforward(d) if pd.notnull(d) else pd.NaT)
        budget_entries_df['adjusted_amount_LC'] = np.where(
            budget_entries_df['cash_type'] == 'Receipt',
            budget_entries_df['amount_LC'],
            -budget_entries_df['amount_LC']
        )

        pivot_df = budget_entries_df.pivot_table(
            index='definition_id',
            columns='period',
            values='adjusted_amount_LC',
            aggfunc="sum",
            fill_value=0,
            dropna=False
        )

        all_periods = pd.date_range(start=date_from, end=date_through, freq=report_period)
        pivot_df = pivot_df.reindex(columns=all_periods, fill_value=0)

        # Ensure columns are in datetime format before formatting
        pivot_df.columns = pd.to_datetime(pivot_df.columns, errors='coerce')
        # Format column headers to show only the date part
        pivot_df.columns = [col.strftime(date_format()) if not pd.isnull(col) else col for col in pivot_df.columns]

        budget_df = pd.merge(definition_df, pivot_df,
                             left_on="id", right_on="definition_id", how="left").fillna(0)
        budget_df.sort_values("key", inplace=True)
        budget_df.drop(columns=["definition_type", "key"], inplace=True)
        budget_df.set_index("id", inplace=True)

        return budget_df

class DetailsView(QWidget):
    def __init__(self, engine, main_view: Budget):
        super().__init__(main_view)
        self.engine = engine
        self.main_view = main_view
        vbox = QVBoxLayout()
        self.field_name = QLabel()
        self.field_name.setStyleSheet("font-size: 20px; font-weight: bold;")
        filterbox = QVBoxLayout()
        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")
        filterbox_from = QHBoxLayout()
        filterbox_through = QHBoxLayout()
        label_dateFrom = QLabel("No datuma")
        self.filter_dateFrom = QDateEdit()
        self.filter_dateFrom.setCalendarPopup(True)
        self.filter_dateFrom.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_dateFrom.setDate(datetime.now())
        self.filter_dateFrom.dateChanged.connect(self.requery)
        filterbox_from.addWidget(label_dateFrom)
        filterbox_from.addWidget(self.filter_dateFrom)
        label_dateThrough = QLabel("Līdz datumam")
        self.filter_dateThrough = QDateEdit()
        self.filter_dateThrough.setCalendarPopup(True)
        self.filter_dateThrough.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_dateThrough.setDate(date(datetime.now().year, 12, 31))
        self.filter_dateThrough.dateChanged.connect(self.requery)
        filterbox_through.addWidget(label_dateThrough)
        filterbox_through.addWidget(self.filter_dateThrough)
        filterbox.addLayout(filterbox_from)
        filterbox.addLayout(filterbox_through)
        label_createAmounts = QLabel("Izveidot atkārtojošos ierakstus")
        label_createAmounts.setStyleSheet("font-weight: bold")
        commandsbox = QVBoxLayout()
        commands_controls = QHBoxLayout()
        commands_buttons = QHBoxLayout()
        label_memo = QLabel("Piezīmes")
        self.text_memo = QLineEdit()
        label_type = QLabel("Tips")
        self.filter_type = QComboBox()
        self.filter_type.addItems(cash_type_map.keys())
        self.filter_type.setCurrentText("Ieņēmums")
        label_amount = QLabel("Summa BV")
        self.text_amount = QLineEdit()
        self.text_amount.setMaximumWidth(100)
        label_frequency = QLabel("Periodiskums")
        self.filter_Frequency = QComboBox(self)
        self.filter_Frequency.addItems(frequency_map.keys())
        self.filter_Frequency.setCurrentText("Mēnesis")
        commands_controls.addWidget(label_memo)
        commands_controls.addWidget(self.text_memo)
        commands_controls.addWidget(label_type)
        commands_controls.addWidget(self.filter_type)
        commands_controls.addWidget(label_amount)
        commands_controls.addWidget(self.text_amount)
        commands_controls.addWidget(label_frequency)
        commands_controls.addWidget(self.filter_Frequency)
        btn_generate = QPushButton("Izveidot")
        btn_generate.clicked.connect(self.generate_amounts)
        btn_delete = QPushButton("Dzēst")
        btn_delete.clicked.connect(self.delete_amounts)
        commands_buttons.addStretch()
        commands_buttons.addWidget(btn_generate)
        commands_buttons.addWidget(btn_delete)
        commandsbox.addLayout(commands_controls)
        commandsbox.addLayout(commands_buttons)
        toolsbox = QHBoxLayout()
        btn_return = QPushButton("Atgriezties uz budžetu")
        btn_return.clicked.connect(self.return_to_budget)
        toolsbox.addStretch()
        toolsbox.addWidget(btn_return)
        label_details = QLabel("Budžeta ieraksti")
        label_details.setStyleSheet("font-weight: bold")
        self.table = ATable()
        action_insert = self.table.context_menu.addAction("Pievienot")
        action_insert.triggered.connect(self.action_insert)
        action_delete = self.table.context_menu.addAction("Dzēst")
        action_delete.triggered.connect(self.action_delete)
        self.table.setModel(DetailsModel(self.table, self.engine))
        type_delegate = EntryTypeDelegate(self.table)
        self.table.setItemDelegateForColumn(0, type_delegate)

        vbox.addWidget(self.field_name)
        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox)
        vbox.addWidget(label_createAmounts)
        vbox.addLayout(commandsbox)
        vbox.addLayout(toolsbox)
        vbox.addWidget(label_details)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        self.table.model().requery()

    def action_insert(self):
        row = self.table.selectedIndexes()[0].row()
        self.table.model().insert(row)

    def action_delete(self):
        row = self.table.selectedIndexes()[0].row()
        self.table.model().delete(row)

    def clear_commandsbox(self):
        self.text_memo.setText("")
        self.text_amount.setText("")
        self.filter_Frequency.setCurrentText("Mēnesis")

    def return_to_budget(self):
        self.main_view.budget_view.requery()

        try:
            df = self.main_view.budget_view.table.model().DATA
            id = self.table.model().definition_id
            row_index = df.index.get_loc(id)
            self.main_view.budget_view.table.selectRow(row_index)
        except Exception as a:
            pass

        self.main_view.refresh_view(0)

    def generate_amounts(self):
        amount = various_to_decimal(self.text_amount.text())
        memo = self.text_memo.text()
        cash_type = cash_type_map[self.filter_type.currentText()]
        definition_id = self.table.model().definition_id
        if amount and definition_id:
            periods = pd.date_range(start = self.filter_dateFrom.date().toPyDate(),
                                    end = self.filter_dateThrough.date().toPyDate(),
                                    freq = frequency_map[self.filter_Frequency.currentText()])

            with Session(self.engine) as session:
                for pdate in periods:
                    entry = BudgetEntry(definition_id=definition_id, cash_type=cash_type,
                                        date=pdate, amount_LC=amount, memo=memo)
                    session.add(entry)
                    session.commit()

        self.requery()

    def delete_amounts(self):
        amount = various_to_decimal(self.text_amount.text())
        definition_id = self.table.model().definition_id
        memo = self.text_memo.text()
        cash_type = cash_type_map[self.filter_type.currentText()]
        if amount and definition_id:
            periods = pd.date_range(start=self.filter_dateFrom.date().toPyDate(),
                                    end=self.filter_dateThrough.date().toPyDate(),
                                    freq=frequency_map[self.filter_Frequency.currentText()])

            with Session(self.engine) as session:
                for pdate in periods:
                    stmt = delete(BudgetEntry).where(BudgetEntry.definition_id==definition_id,
                                                    BudgetEntry.date==pdate, BudgetEntry.cash_type==cash_type,
                                                    BudgetEntry.amount_LC==amount, BudgetEntry.memo==memo)
                    session.execute(stmt)
                    session.commit()

        self.requery()

frequency_map = {
            "Diena": "D",
            "Nedēļa": "W-SUN",
            "Mēnesis": "ME",
            "Kvartāls": "QE",
            "Gads": "YE"
        }

offset_map = {
            "D": pd.offsets.Day(0),
            "W-SUN": pd.offsets.Week(weekday=6),  # Sunday
            "ME": pd.offsets.MonthEnd(0),
            "QE": pd.offsets.QuarterEnd(startingMonth=12),
            "YE": pd.offsets.YearEnd(0)
        }


cash_type_map = {
            "Ieņēmums": "Receipt",
            "Maksājums": "Payment"
        }

class EntryTypeDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(cash_type_map.keys())
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class DetailsModel(ATableModel):
    definition_id = None
    EMPTY_ROW_AT_BOTTOM = True

    def _do_requery(self):
        date_from = self.parent().parent().filter_dateFrom.date().startOfDay().toPyDateTime()
        date_through = self.parent().parent().filter_dateThrough.date().endOfDay().toPyDateTime()
        # python_datetime = self.date_edit.date().startOfDay().toPyDateTime()
        stmt = select(BudgetEntry.id,
                      BudgetEntry.cash_type,
                      BudgetEntry.date,
                      BudgetEntry.amount_LC,
                      BudgetEntry.memo) \
            .order_by(BudgetEntry.date, BudgetEntry.id)
        # print("from: " + str(date_from) + " through: " + str(date_through))
        stmt = stmt.filter(BudgetEntry.definition_id == self.definition_id,
                           BudgetEntry.date >= date_from, BudgetEntry.date <= date_through)

        with Session(self.engine) as session:
            dataset = session.execute(stmt).all()

            # Convert to DataFrame
            data = pd.DataFrame(dataset, columns=["id", "Tips", "Datums", "Summa BV", "Piezīmes"])
            data.set_index("id", inplace=True)
            return data

    def rowCount(self, parent=None):
        if self.definition_id:
            return super().rowCount(parent)
        else:
            return 0

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def set_definition_id(self, id):
        self.definition_id = various_to_integer(id)
        # print(f"definition_id = {self.definition_id}")

    def _get_value(self, index):
        if self.get_column_index("Tips") == index.column():
            rev_map = {v: k  for k, v in cash_type_map.items()}
            value = super()._get_value(index)
            return rev_map.get(value)
        else:
            return super()._get_value(index)

    def _generate_default_row(self):
        """
            Generate a default row on insert(), INSERT INTO database, assign INDEX.
            return as DataFrame compatible with self.DATA
        """
        with Session(self.engine) as session:
            entry = BudgetEntry(definition_id=self.definition_id)
            session.add(entry)
            session.commit()

            # Convert to DataFrame
            new_record = pd.DataFrame([[None, None, None, None]],
                                      columns=["Tips", "Datums", "Summa BV", "Piezīmes"], index=[entry.id])

            return new_record

    def _cast_input_to_value(self, index, value_str: str):
        """
        Casts user input on setData to DATABASE compatible value.

        :param index: cell index
        :param value_str: value in string format
        :return: value of correct datatype
        """
        if self.get_column_index("Summa BV") == index.column():
            return various_to_decimal(value_str)
        elif self.get_column_index("Datums") == index.column():
            return str_to_date(value_str)
        elif self.get_column_index("Tips") == index.column():
            return cash_type_map.get(value_str)
        else:
            return str(value_str)

    def _set_data_in_database(self, index, value):
        """
        Updates DATABASE on setData. You should override this method.

        :param index: cell index
        :param value: value of correct data type
        :return:
        """
        entry_id = various_to_integer(self.DATA.index[index.row()])

        with Session(self.engine) as session:
            stmt = select(BudgetEntry).where(BudgetEntry.id == entry_id)
            entry = session.scalars(stmt).first()

            if self.get_column_index("Tips") == index.column():
                entry.cash_type = value
            elif self.get_column_index("Datums") == index.column():
                entry.date = value
            elif self.get_column_index("Summa BV") == index.column():
                entry.amount_LC = value
            elif self.get_column_index("Piezīmes") == index.column():
                entry.memo = value

            session.commit()

    def _delete_row_in_database(self, row):
        """
        Delete selected row in DATABASE.
        You should override this method.

        :param row: row index
        :return:
        """
        entry_id = various_to_integer(self.DATA.index[row])
        with Session(self.engine) as session:
            stmt = delete(BudgetEntry).where(BudgetEntry.id == entry_id)
            session.execute(stmt)
            session.commit()