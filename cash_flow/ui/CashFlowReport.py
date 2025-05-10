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
            "Diena": "day",
            "Nedēļa": "week",
            "Mēnesis": "month",
            "Kvartāls": "quarter",
            "Gads": "year"
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
            # print(f"Data exported to {file_name} with formatting.")

class CashFlowReportModel(ATableModel):

    def _do_requery(self):

        # Setup filters
        date_from = self.FILTER["date from"].strftime("%Y-%m-%d")
        date_through = self.FILTER["date through"].strftime("%Y-%m-%d")
        period = self.FILTER["frequency"]

        # Mapping period to offset (end of period)
        period_offsets = {
            "day": pd.offsets.Day(0),
            "week": pd.offsets.Week(weekday=6),  # Sunday
            "month": pd.offsets.MonthEnd(0),
            "quarter": pd.offsets.QuarterEnd(startingMonth=12),
            "year": pd.offsets.YearEnd(0)
        }
        date_offset = period_offsets.get(period, pd.offsets.MonthEnd(0))
        date_freq = {
            "day": "D",
            "week": "W-SUN",  # Sunday
            "month": "ME",
            "quarter": "QE",
            "year": "YE"
        }
        date_frequency = date_freq.get(period, "ME")

        # Load all data from database

        actual = pd.read_sql_query(
            'SELECT * FROM G10_CashFlow_Actual_Corresponding WHERE d_date >= "' + date_from + '" AND d_date <= "' + date_through + '" ',
            self.engine)
        pending = pd.read_sql_query(
            'SELECT * FROM G12_CashFlow_Pending_Corresponding WHERE p_date >= "' + date_from + '" AND p_date <= "' + date_through + '" ',
            self.engine)
        budgeted = pd.read_sql_query(
            'SELECT * FROM F01_BudgetEntries WHERE date >= "' + date_from + '" AND date <= "' + date_through + '" ',
            self.engine)
        cash = pd.read_sql_query('SELECT * FROM G02_CashTransactions WHERE d_date <= "' + date_through + '" ', self.engine)
        definition_df = pd.read_sql_table("E01_CashFlowDefinition", self.engine)

        definition_accounts_df = pd.read_sql_table("E01_CashFlowDefinitionAccounts", self.engine)
        definition_totals_df = pd.read_sql_table("E01_CashFlowDefinitionTotals", self.engine)

        # Ensure required columns and formats

        actual['period_end'] = pd.to_datetime(actual['d_date'], format='mixed') + date_offset
        actual['cf_amount'] = np.where(actual['gl_entry_type'] == 'CR', actual['gl_amount_LC'], -actual['gl_amount_LC'])
        pending['period_end'] = pd.to_datetime(pending['p_date'], format='mixed') + date_offset
        pending['cf_amount'] = np.where(pending['gl_entry_type'] == 'CR', pending['gl_amount_LC'],
                                        -pending['gl_amount_LC'])
        budgeted['period_end'] = pd.to_datetime(budgeted['date'], format='mixed') + date_offset
        budgeted['cf_amount'] = np.where(budgeted['cash_type'] == 'Receipt', budgeted['amount_LC'],
                                         -budgeted['amount_LC'])
        cash['period_end'] = pd.to_datetime(cash['d_date'], format='mixed') + date_offset
        cash['cf_amount'] = np.where(cash['gl_entry_type'] == 'DR', cash['gl_amount_LC'], -cash['gl_amount_LC'])

        definition_df.rename(columns={"id": "definition_id"}, inplace=True)
        definition_acc_df = definition_df[definition_df["definition_type"] == 1]
        definition_tot_df = definition_df[definition_df["definition_type"] == 2]
        definition_bal_df = definition_df[definition_df["definition_type"] == 3]

        # -------------------------------------------------------------------
        # ************** (1) CashFlow based on accounts definitions *********
        # -------------------------------------------------------------------

        #  Prepare chart of CF definitions

        # Merge accounts into accounts definition
        definition_accounts_df = pd.merge(
            definition_acc_df,
            definition_accounts_df,
            on="definition_id", how="left")
        definition_accounts_df.drop(columns=["id"], inplace=True)

        actual = pd.merge(definition_accounts_df,
                          actual,
                          left_on=['cash_type', 'account'],  # Columns in definition_df
                          right_on=['cash_type', 'gl_account'],  # Corresponding columns in transactions_df
                          how='left'
                          )

        pending = pd.merge(definition_accounts_df,
                           pending,
                           left_on=['cash_type', 'account'],  # Columns in definition_df
                           right_on=['cash_type', 'gl_account'],  # Corresponding columns in transactions_df
                           how='left'
                           )

        budgeted = pd.merge(definition_acc_df,
                            budgeted,
                            left_on=['definition_id'],  # Columns in definition_df
                            right_on=['definition_id'],  # Corresponding columns in transactions_df
                            how='left'
                            )

        # -------------------
        # GROUP & MERGE
        # -------------------
        def get_period_totals(df, label):
            grouped = df.groupby(['definition_id', 'period_end', 'cash_type'])['cf_amount'].sum().unstack(fill_value=0)
            columns = ["Receipt", "Payment"]
            grouped = grouped.reindex(columns=columns, fill_value=0)
            grouped.columns = [f"{label}_{col}" for col in grouped.columns]
            return grouped

        actual_period = get_period_totals(actual, 'Actual')
        pending_period = get_period_totals(pending, 'Pending')
        budgeted_period = get_period_totals(budgeted, 'Budgeted')

        # Combine all
        combined = actual_period.join(pending_period, how='outer') \
            .join(budgeted_period, how='outer') \
            .fillna(0).reset_index()

        # -------------------
        # SPLIT PAST / FUTURE
        # -------------------
        today = pd.to_datetime(date.today())
        this_period_end = today + date_offset

        # Split
        past = combined[combined['period_end'] < this_period_end]
        future = combined[combined['period_end'] >= this_period_end]

        # -------------------
        # CASHFLOW LOGIC
        # -------------------

        # For past: use only actuals
        past['income'] = past.get('Actual_Receipt', 0)
        past['expense'] = past.get('Actual_Payment', 0)

        # For future: use max(budgeted, actual+pending)
        future['actual_plus_pending_income'] = future.get('Actual_Receipt', 0) + future.get('Pending_Receipt', 0)
        future['actual_plus_pending_expense'] = future.get('Actual_Payment', 0) + future.get('Pending_Payment', 0)

        future['income'] = future[['Budgeted_Receipt', 'actual_plus_pending_income']].max(axis=1)
        future['expense'] = future[['Budgeted_Payment', 'actual_plus_pending_expense']].min(axis=1)

        # Combine
        cashflow = pd.concat([past, future], ignore_index=True)
        cashflow['net_cashflow'] = cashflow['income'] + cashflow['expense']

        # -------------------
        # CASHFLOW OUTPUT
        # -------------------

        # Pivot first
        pivot_cf = cashflow.pivot_table(
            index='definition_id',
            columns='period_end',
            values='net_cashflow',
            aggfunc='sum'
        ).fillna(0)

        # Fill missing periods

        # Build full period range
        min_period = cashflow['period_end'].min()
        max_period = cashflow['period_end'].max()

        all_periods = pd.date_range(start=min_period, end=max_period, freq=date_frequency)

        # Reindex pivot to include all periods
        pivot_cf = pivot_cf.reindex(columns=all_periods, fill_value=0)

        # Sort columns just in case
        pivot_cf = pivot_cf.sort_index(axis=1)

        # Ensure 0 instead of NaN in empty cells
        pivot_cf = pd.merge(definition_acc_df["definition_id"], pivot_cf, left_on="definition_id",
                            right_on="definition_id", how="left").fillna(0)
        pivot_cf.set_index("definition_id", inplace=True)

        # -----------------------------------------------------------------------------------------------------------------
        # ********************** (2) Start working with totals based on totaled definitions *******************************
        # -----------------------------------------------------------------------------------------------------------------

        # Merge totals into totals definition
        definition_totals_df = pd.merge(
            definition_tot_df,
            definition_totals_df,
            on="definition_id", how="left")
        definition_totals_df.drop(columns=["id"], inplace=True)

        # Merge totals definition with summarized accounts pivot

        merged_totals = pd.merge(definition_totals_df,
                                 pivot_cf,
                                 left_on='definition_summarized',
                                 right_on='definition_id',
                                 how='left'
                                 )

        # Drop unnecessary columns

        merged_totals.drop(columns=['key', 'definition_type', 'name', 'definition_summarized'], inplace=True)

        # Choose value_columns for further summarization

        value_columns = [col for col in merged_totals.columns if col not in ['definition_id']]

        # Summarize value_columns based on group value

        summarized_totals = merged_totals.groupby('definition_id', group_keys=False)[value_columns].sum()

        # .reset_index()

        summarized_totals.fillna(0, inplace=True)

        # ------------------------------------------------------------------------------------------------------------
        # ********************** (3) Start working with balances on end of each period *******************************
        # ------------------------------------------------------------------------------------------------------------

        # ----------------------------
        # STEP 1: Prepare actual_bank
        # ----------------------------

        # Group and sort actual bank balance by period
        cash_by_period = cash.groupby('period_end')['cf_amount'].sum().sort_index()
        cumulative_cash = cash_by_period.cumsum()

        # ----------------------------
        # STEP 2: Determine cutoff
        # ----------------------------

        # All period_end columns from pivot_cf
        all_periods = pivot_cf.columns.sort_values()

        # Identify past and future periods
        past_periods = all_periods[all_periods < this_period_end]
        future_periods = all_periods[all_periods >= this_period_end]

        # ----------------------------
        # STEP 3: Build closing balance series
        # ----------------------------

        # Closing balance for past: from cumulative actual bank
        past_closing = cumulative_cash.reindex(past_periods, method='ffill').fillna(0)

        # Starting point for future: last known balance
        last_past_balance = past_closing.iloc[-1] if not past_closing.empty else 0

        # Future cashflows from pivot_cf
        cashflow_by_period = pivot_cf.sum(axis=0)

        # Compute future balances
        future_closing = {}
        balance = last_past_balance
        for period in future_periods:
            balance += cashflow_by_period.get(period, 0)
            future_closing[period] = balance

        # Combine both into full closing balance series
        full_closing_balance = pd.Series(dtype=float)
        full_closing_balance = pd.concat([
            past_closing,
            pd.Series(future_closing)
        ]).reindex(all_periods, fill_value=0)

        # Create a new DataFrame with closing balances only
        balances = pd.DataFrame(
            [full_closing_balance],  # one row
            index=[0]  # index = 0
        )

        # Create a new DataFrame with repeated rows for each definition_id
        balances = pd.merge(definition_bal_df["definition_id"], balances, how='cross')
        balances = balances.set_index("definition_id")

        # ---------------------------------------------------------------------------------------------------------------------------------------
        # ********************** (4) Put together summarized accounts, totals and balances on end of each period *******************************
        # ---------------------------------------------------------------------------------------------------------------------------------------

        # Concatenate it all together
        report = pd.concat([pivot_cf, summarized_totals, balances])

        # -------------------------------------
        # Prepare report for visual appearance
        # -------------------------------------

        # Merge report definition header with report
        report = pd.merge(definition_df, report, left_on="definition_id", right_on="definition_id", how="left")

        # Sort based on key value
        report.sort_values("key", inplace=True)

        # Subtract report formatting in separate dataframe
        format_df = report["definition_type"]

        # Prepare report_df for visual appearance

        report.drop(columns=["definition_id", "key", "definition_type"], inplace=True)
        report.set_index("name", inplace=True)

        # Format column headers to show only the date part
        report.columns = [col.strftime(date_format()) if not pd.isnull(col) else col for col in report.columns]

        self.FORMAT = format_df
        return report



    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                value = self.DATA.columns[section]
                return self._format_value(value, role)
            return None
        elif orientation == Qt.Orientation.Vertical:
            if role == Qt.ItemDataRole.DisplayRole:
                value = self.DATA.index[section]
                return self._format_value(value, role)
            elif role == Qt.ItemDataRole.BackgroundRole:
                if self.FORMAT.iloc[section] == 2:  # Totals
                    return QBrush(Qt.GlobalColor.darkBlue)
                elif self.FORMAT.iloc[section] == 3: # Balances
                    return QBrush(Qt.GlobalColor.darkCyan)
                return None
            return None
        return None

    def _format_background(self, index, role=Qt.ItemDataRole.BackgroundRole):
        def_type = self.FORMAT.iloc[index.row()]
        if role == Qt.ItemDataRole.BackgroundRole:
            if def_type == 2: # Totals
                return QBrush(Qt.GlobalColor.darkBlue)
            elif def_type == 3: # Balances
                return QBrush(Qt.GlobalColor.darkCyan)
            return None
        return None