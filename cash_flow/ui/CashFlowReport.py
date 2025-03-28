from datetime import date, datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QLabel, QComboBox, QPushButton, QFileDialog

import pandas as pd
import numpy as np
from openpyxl.reader.excel import load_workbook
from openpyxl.styles import Alignment, PatternFill, Font

from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import date_format



class CashFlowReport(QWidget):

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        vbox = QVBoxLayout()
        toolbox = QHBoxLayout()
        btn_excel = QPushButton("Export to Excel")
        btn_excel.clicked.connect(self.export_to_excel)
        toolbox.addStretch()
        toolbox.addWidget(btn_excel)
        filterbox_from = QHBoxLayout()
        filterbox_through = QHBoxLayout()
        filterbox_freq = QHBoxLayout()
        label_filter = QLabel("Filtrs")
        label_filter.setStyleSheet("font-weight: bold")
        label_dateFrom = QLabel("No datuma")
        self.filter_dateFrom = QDateEdit()
        self.filter_dateFrom.setCalendarPopup(True)
        self.filter_dateFrom.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_dateFrom.setDate(date(datetime.now().year, 1, 1))
        self.filter_dateFrom.dateChanged.connect(self.requery)
        filterbox_from.addWidget(label_dateFrom)
        filterbox_from.addWidget(self.filter_dateFrom)
        label_dateThrough = QLabel("Līdz datumam")
        self.filter_dateThrough = QDateEdit()
        self.filter_dateThrough.setCalendarPopup(True)
        self.filter_dateThrough.setDisplayFormat("dd.MMMM.yyyy")
        self.filter_dateThrough.setDate(datetime.now())
        self.filter_dateThrough.dateChanged.connect(self.requery)
        filterbox_through.addWidget(label_dateThrough)
        filterbox_through.addWidget(self.filter_dateThrough)
        label_freq = QLabel("Periodiskums")
        self.freq_map = {
            "Nedēļa": "W-SUN",
            "Mēnesis": "M",
            "Kvartāls": "Q",
            "Gads": "Y"
        }
        self.filter_Frequency = QComboBox(self)
        self.filter_Frequency.addItems(self.freq_map.keys())
        self.filter_Frequency.setCurrentText("Mēnesis")
        self.filter_Frequency.currentIndexChanged.connect(self.requery)
        filterbox_freq.addWidget(label_freq)
        filterbox_freq.addWidget(self.filter_Frequency)
        label_cashflow = QLabel("Naudas plūsma")
        label_cashflow.setStyleSheet("font-weight: bold")
        self.table = ATable()
        self.table.setModel(CashFlowReportModel(self.table, self.engine))

        vbox.addLayout(toolbox)
        vbox.addWidget(label_filter)
        vbox.addLayout(filterbox_from)
        vbox.addLayout(filterbox_through)
        vbox.addLayout(filterbox_freq)
        vbox.addWidget(label_cashflow)
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.requery()

    def requery(self):
        selected_freq = self.filter_Frequency.currentText()
        freq = self.freq_map[selected_freq]
        self.table.model().set_filter({"date from": self.filter_dateFrom.date().toPyDate(),
                                       "date through": self.filter_dateThrough.date().toPyDate(),
                                       "frequency": freq})

    def export_to_excel(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)")

        if file_name:
            if not file_name.endswith(".xlsx"):
                file_name += ".xlsx"
            # Save DataFrame to Excel
            self.table.model().DATA.to_excel(file_name, index=True)

            # Load workbook for formatting
            wb = load_workbook(file_name)
            ws = wb.active

            # Align entire first column (Index) to left
            for row in range(1, ws.max_row + 1):
                ws.cell(row=row, column=1).alignment = Alignment(horizontal="left")

            # Formatting row colors
            dark_blue_fill = PatternFill(start_color="00008B", end_color="00008B", fill_type="solid")
            dark_cyan_fill = PatternFill(start_color="008B8B", end_color="008B8B", fill_type="solid")
            # Define font for white text
            white_font = Font(color="FFFFFF")

            row = 1 # First row for column headers
            for def_type in self.table.model().FORMAT:
                row = row + 1
                if def_type == 2:  # Totals
                    for cell in ws[row]:
                        cell.fill = dark_blue_fill
                        cell.font = white_font
                elif def_type == 3:  # Balances
                    for cell in ws[row]:
                        cell.fill = dark_cyan_fill
                        cell.font = white_font

            wb.save(file_name)
            print(f"Data exported to {file_name} with formatting.")

class CashFlowReportModel(ATableModel):

    def requery(self):
        self.beginResetModel()

        # Setup filters
        date_from = self.FILTER["date from"].strftime("%Y-%m-%d")
        date_through = self.FILTER["date through"].strftime("%Y-%m-%d")
        report_period = self.FILTER["frequency"]

        # Load all data from database

        bank_df = pd.read_sql_query(
            'SELECT * FROM D13_CF_Bank_Union WHERE d_date >= "' + date_from + '" AND d_date <= "' + date_through + '" ',
            self.engine)
        cash_df = pd.read_sql_query('SELECT * FROM D10_Cash_Transactions WHERE d_date <= "' + date_through + '" ',
                                    self.engine)
        definition_df = pd.read_sql_table("E01_CashFlowDefinition", self.engine)
        definition_df.rename(columns={"id": "definition_id"}, inplace=True)
        definition_acc_df = definition_df[definition_df["definition_type"] == 1]
        definition_tot_df = definition_df[definition_df["definition_type"] == 2]
        definition_bal_df = definition_df[definition_df["definition_type"] == 3]
        definition_accounts_df = pd.read_sql_table("E01_CashFlowDefinitionAccounts", self.engine)
        definition_totals_df = pd.read_sql_table("E01_CashFlowDefinitionTotals", self.engine)

        # ********************** (1) Start working with sums based on filtered accounts *******************************
        # Merge accounts into accounts definition

        definition_accounts_df = pd.merge(
            definition_acc_df,
            definition_accounts_df,
            on="definition_id", how="left")
        definition_accounts_df.drop(columns=["id"], inplace=True)

        # Merge accounts definition into bank transactions

        merged_df = pd.merge(definition_accounts_df,
                             bank_df,
                             left_on=['entry_type', 'account'],  # Columns in definition_df
                             right_on=['gl_entry_type', 'gl_account'],  # Corresponding columns in transactions_df
                             how='left'
                             )

        # Add column adjusted_amount_LC based on operator + / -

        merged_df['adjusted_amount_LC'] = np.where(
            merged_df['operator'] == '+',
            merged_df['gl_amount_LC'],
            -merged_df['gl_amount_LC']
        )

        # Convert d_date to_datetime if not done yet

        merged_df['d_date'] = pd.to_datetime(merged_df['d_date'])

        # Convert adjusted_amount_LC to_numeric if not done yet

        merged_df['adjusted_amount_LC'] = pd.to_numeric(merged_df['adjusted_amount_LC'], errors='coerce')

        # Add column for period reference

        merged_df["d_period"] = merged_df['d_date'].dt.to_period(report_period).apply(
            lambda r: r.to_timestamp(how='end').normalize() if pd.notna(r) else pd.NaT)

        # Pivot values based on definition_id and d_period

        pivot_df = merged_df.pivot_table(
            index='definition_id',
            columns='d_period',
            values='adjusted_amount_LC',
            aggfunc="sum",
            fill_value=0,
            dropna=False
        )
        # Add all periods in range if some are missing

        all_periods = pd.date_range(start=date_from, end=date_through, freq=report_period)
        pivot_df = pivot_df.reindex(columns=all_periods, fill_value=0)

        # Ensure columns are in datetime format before formatting
        pivot_df.columns = pd.to_datetime(pivot_df.columns, errors='coerce')


        # ********************** (2) Start working with totals based on totaled definitions *******************************
        # Merge totals into totals definition
        definition_totals_df = pd.merge(
            definition_tot_df,
            definition_totals_df,
            on="definition_id", how="left")
        definition_totals_df.drop(columns=["id"], inplace=True)

        # Merge totals definition with summarized accounts pivot

        merged_totals_df = pd.merge(definition_totals_df,
                                    pivot_df,
                                    left_on='definition_summarized',
                                    right_on='definition_id',
                                    how='left'
                                    )

        # Add multiplication num for operator

        merged_totals_df['op_num'] = merged_totals_df['operator'].map({'+': 1, '-': -1})

        # Drop unnecessary columns

        merged_totals_df.drop(columns=['key', 'definition_type', 'name', 'operator', 'definition_summarized'],
                              inplace=True)

        # Choose value_columns for further summarization

        value_columns = [col for col in merged_totals_df.columns if col not in ['definition_id', 'op_num']]

        # Summarize value_columns based on group value and op_num

        summarized_totals_df = (
            merged_totals_df.groupby('definition_id', group_keys=False)[value_columns + ['op_num']]
            .apply(lambda group: pd.Series(
                (group['op_num'].to_numpy()[:, None] * group[value_columns].to_numpy()).sum(axis=0),
                index=value_columns
            ))
            # .reset_index()
        )
        summarized_totals_df.fillna(0, inplace=True)
        # ********************** (3) Start working with balances on end of each period *******************************

        # Convert d_date to_datetime if not yet
        cash_df['d_date'] = pd.to_datetime(cash_df['d_date'])

        # Initialize cumulative balance
        cumulative_balance = 0
        balances = []

        # Start index for efficient filtering
        start_idx = 0

        for eoperiod in value_columns:
            # Filter only new transactions from the last weekend up to the current one
            new_transactions = cash_df[(cash_df.index >= start_idx) & (cash_df['d_date'] <= eoperiod)]

            # If there are new transactions, update cumulative balance
            if not new_transactions.empty:
                cumulative_balance += new_transactions.apply(
                    lambda row: row['gl_amount_LC'] if row['gl_entry_type'] == 'DR' else -row['gl_amount_LC'], axis=1
                ).sum()

                # Move the start index forward to avoid redundant calculations
                start_idx = new_transactions.index[-1] + 1

                # Store balance for the current weekend
            balances.append(cumulative_balance)

        # Create a DataFrame with periods as columns
        balances_df = pd.DataFrame([balances], columns=value_columns)

        # Create a new DataFrame with repeated rows for each definition_id
        balances_df = pd.merge(definition_bal_df["definition_id"], balances_df, how='cross')
        balances_df = balances_df.set_index("definition_id")

        # ********************** (3) Put together summarized accounts, totals and balances on end of each period *******************************

        # Concatenate it all together
        report_df = pd.concat([pivot_df, summarized_totals_df, balances_df])

        # ********************** (4) Prepare report for visual appearance *******************************

        # Merge report definition header with report
        report_df = pd.merge(definition_df, report_df, left_on="definition_id", right_on="definition_id", how="left")

        # Sort based on key value
        report_df.sort_values("key", inplace=True)

        # Subtract report formatting in separate dataframe
        format_df = report_df["definition_type"]

        # Prepare report_df for visual appearance

        report_df.drop(columns=["definition_id", "key", "definition_type"], inplace=True)
        report_df.set_index("name", inplace=True)

        # Format column headers to show only the date part
        report_df.columns = [col.strftime(date_format()) if not pd.isnull(col) else col for col in report_df.columns]

        self.FORMAT = format_df
        self.DATA = report_df

        self.endResetModel()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                value = self.DATA.columns[section]
                return self._format_value(value, role)
        elif orientation == Qt.Orientation.Vertical:
            if role == Qt.ItemDataRole.DisplayRole:
                value = self.DATA.index[section]
                return self._format_value(value, role)
            elif role == Qt.ItemDataRole.BackgroundRole:
                if self.FORMAT.iloc[section] == 2:  # Totals
                    return QBrush(Qt.GlobalColor.darkBlue)
                elif self.FORMAT.iloc[section] == 3: # Balances
                    return QBrush(Qt.GlobalColor.darkCyan)

    def _format_background(self, index, role=Qt.ItemDataRole.BackgroundRole):
        def_type = self.FORMAT.iloc[index.row()]
        if role == Qt.ItemDataRole.BackgroundRole:
            if def_type == 2: # Totals
                return QBrush(Qt.GlobalColor.darkBlue)
            elif def_type == 3: # Balances
                return QBrush(Qt.GlobalColor.darkCyan)