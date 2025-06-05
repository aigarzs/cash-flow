import datetime

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog

from cash_flow.ui.AWidgets import ATable, ATableModel
from cash_flow.util.Converters import decimal_format


class Browse_PendingReceipt(QWidget):
    def __init__(self, engine, return_method):
        super().__init__(None)
        self.engine = engine
        vbox = QVBoxLayout()

        toolbox = QHBoxLayout()
        btn_return = QPushButton("Atgriezties")
        btn_return.clicked.connect(return_method)
        btn_export_excel = QPushButton("Eksportēt uz Excel")
        btn_export_excel.clicked.connect(self.export_to_excel)
        toolbox.addWidget(btn_return)
        toolbox.addStretch()
        toolbox.addWidget(btn_export_excel)

        totalsbox = QHBoxLayout()
        label_totals = QLabel("Kopā BV: ")
        label_amount = QLabel()
        totalsbox.addStretch()
        totalsbox.addWidget(label_totals)
        totalsbox.addWidget(label_amount)

        self.label_name = QLabel("Sagaidāmie ieņēmumi")
        self.table = ATable()
        self.table.setModel(PendingReceiptModel(self.table, self.engine, label_amount))

        vbox.addLayout(toolbox)
        vbox.addWidget(self.label_name)
        vbox.addWidget(self.table)
        vbox.addLayout(totalsbox)
        self.setLayout(vbox)
        #self.requery()

    def requery(self):
        self.table.model().set_filter({"Date_From": None, "Date_Through": None, "Frequency": None, "Definition_ID": None, "Period_End": None})

    def export_to_excel(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)")

        if file_name:
            if not file_name.endswith(".xlsx"):
                file_name += ".xlsx"
            # Save DataFrame to Excel
            self.table.model().DATA.to_excel(file_name, index=True)



class PendingReceiptModel(ATableModel):
    def __init__(self, table, engine, totals: QLabel):
        super().__init__(table, engine)
        self.totals = totals

    def _do_requery(self):
        # print(self.FILTER)
        date_from = self.FILTER.get("Date_From", datetime.date.today())
        date_through = self.FILTER.get("Date_Through", datetime.date.today())
        frequency = self.FILTER.get("Frequency", "month")
        period_end = pd.to_datetime(self.FILTER["Period_End"])
        definition_id = self.FILTER.get("Definition_ID", 0)

        period_offsets = {
            "day": pd.offsets.Day(0),
            "week": pd.offsets.Week(weekday=6),  # Sunday
            "month": pd.offsets.MonthEnd(0),
            "quarter": pd.offsets.QuarterEnd(startingMonth=12),
            "year": pd.offsets.YearEnd(0)
        }
        date_offset = period_offsets.get(frequency, pd.offsets.MonthEnd(0))

        # handling sqlite issues with datetime timepart
        next_day_date_through = (pd.to_datetime(date_through) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        previous_day_date_from = (pd.to_datetime(date_from) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')

        transactions = pd.read_sql_query("SELECT * FROM G12_CashFlow_Pending_Corresponding WHERE p_date > '" + previous_day_date_from +
                                         "' AND p_date < '" + next_day_date_through + "'", self.engine)
        definition = pd.read_sql_table("E01_CashFlowDefinitionAccounts", self.engine)
        customers = pd.read_sql_table("B04_Customers", self.engine)
        vendors = pd.read_sql_table("B05_Vendors", self.engine)
        doctypes = pd.read_sql_table("D02_DocTypes", self.engine)
        cash_types = pd.DataFrame({"cf_type": ["Receipt", "Payment"], "cf_type_translated": ["Ieņēmums", "Maksājums"]})
        cash_statuses = pd.DataFrame({"cf_status": ["Actual", "Pending", "Budgeted"],
                                      "cf_status_translated": ["Faktiski", "Sagaidāmi", "Budžets"]})

        # print(f"definition_id: {definition_id}")
        definition = definition[definition["definition_id"] == definition_id]
        definition = definition.drop(columns = ["id"])
        # print(definition)
        transactions = definition.merge(transactions, left_on = ["cash_type", "account"], right_on = ["cash_type", "gl_account"], how="left")
        transactions["p_date"] = pd.to_datetime(transactions['p_date'], format='mixed', errors='coerce')
        transactions["period_end"] = transactions["p_date"].apply(lambda d: date_offset.rollforward(d) if pd.notnull(d) else pd.NaT)
        transactions = transactions.merge(customers[["id", "name"]], left_on = "d_customer_id", right_on = "id", how = "left")
        transactions = transactions.merge(vendors[["id", "name"]], left_on = "d_vendor_id", right_on = "id", how = "left")
        transactions = transactions.merge(doctypes, left_on = "d_type", right_on = "id", how = "left")
        transactions = transactions.merge(cash_types, left_on = "cash_type", right_on = "cf_type", how = "left")
        transactions = transactions.merge(cash_statuses, left_on = "cash_status", right_on = "cf_status", how = "left")
        transactions = transactions[transactions["period_end"] == period_end]
        transactions = transactions[transactions["cash_type"] == "Receipt"]
        transactions = transactions.reindex(columns=["d_id", "period_end", "cf_type_translated", "cf_status_translated", "name", "p_date", "d_number",
                                                     "name_x", "name_y", "d_description", "gl_entry_type", "gl_account",
                                                     "d_currency", "gl_amount", "gl_amount_LC"])
        transactions.columns = ["d_id", "Periods", "NP Tips", "NP Statuss", "Dok. Tips", "Datums", "Dok. Numurs",
                                "Klients", "Piegādātājs", "Dok. Apraksts", "VG Tips", "VG Konts",
                                "Valūta", "Summa", "Summa BV"]
        transactions = transactions.set_index("d_id")

        total = (np.where(transactions["VG Tips"] == "CR", 1, -1) * transactions["Summa BV"]).sum()
        self.totals.setText(decimal_format().format(total))

        return transactions

