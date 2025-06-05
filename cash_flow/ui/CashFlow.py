import sys

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication

import cash_flow.util.Settings
from cash_flow.database.AEngine import engine
from cash_flow.ui.Budget import Budget
from cash_flow.ui.CashFlowReport import CashFlowReport
from cash_flow.ui.CashFlowDefinition import CashFlowDefinition
from cash_flow.ui.Customers import Customers
from cash_flow.ui.CustomersCreditnotes import CustomersCreditnotes
from cash_flow.ui.CustomersInvoicesCleared import CustomersInvoicesCleared
from cash_flow.ui.CustomersInvoicesUncleared import CustomersInvoicesUncleared
from cash_flow.ui.CustomersPayments import CustomersPayments
from cash_flow.ui.Demo import Demo
from cash_flow.ui.Vendors import Vendors
from cash_flow.ui.VendorsCreditnotes import VendorsCreditnotes
from cash_flow.ui.VendorsInvoicesCleared import VendorsInvoicesCleared
from cash_flow.ui.VendorsInvoicesUncleared import VendorsInvoicesUncleared
from cash_flow.ui.VendorsPayments import VendorsPayments


class CashFlow(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.ui = uic.loadUi("CashFlow.ui")
        self.engine = engine
        self.setup_ui()
        self.setup_translations()
        self.ui.show()
        self.open_CashFlowDefinition()

    def setup_ui(self):
        tabs = self.ui.tabWidget
        tabs.tabCloseRequested.connect(lambda index: tabs.removeTab(index))

        self.ui.button_CustomersInvoicesUncleared.clicked.connect(self.open_CustomersInvoicesUncleared)
        self.ui.button_CustomersInvoicesCleared.clicked.connect(self.open_CustomersInvoicesCleared)
        self.ui.button_CustomersPayments.clicked.connect(self.open_CustomersPayments)
        self.ui.button_CustomersCreditnotes.clicked.connect(self.open_CustomersCreditnotes)
        self.ui.button_Customers.clicked.connect(self.open_Customers)
        self.ui.button_Vendors.clicked.connect(self.open_Vendors)
        self.ui.button_VendorsInvoicesUncleared.clicked.connect(self.open_VendorsInvoicesUncleared)
        self.ui.button_VendorsInvoicesCleared.clicked.connect(self.open_VendorsInvoicesCleared)
        self.ui.button_VendorsPayments.clicked.connect(self.open_VendorsPayments)
        self.ui.button_VendorsCreditnotes.clicked.connect(self.open_VendorsCreditnotes)
        self.ui.button_CashFlowReport.clicked.connect(self.open_CashFlowReport)
        self.ui.button_CashFlowDefinition.clicked.connect(self.open_CashFlowDefinition)
        self.ui.button_Budget.clicked.connect(self.open_Budget)
        

    def setup_translations(self):
        pass


    def open_Budget(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(Budget(self.engine), "Budžets")
        tabs.setCurrentIndex(i)

    def open_CustomersInvoicesUncleared(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(CustomersInvoicesUncleared(self.engine), "Neapmaksātie klientu rēķini")
        tabs.setCurrentIndex(i)

    def open_CustomersInvoicesCleared(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(CustomersInvoicesCleared(self.engine), "Apmaksātie klientu rēķini")
        tabs.setCurrentIndex(i)

    def open_CustomersPayments(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(CustomersPayments(self.engine), "Klientu maksājumi")
        tabs.setCurrentIndex(i)

    def open_CustomersCreditnotes(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(CustomersCreditnotes(self.engine), "Klientu kredītrēķini")
        tabs.setCurrentIndex(i)

    def open_Customers(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(Customers(self.engine), "Klienti")
        tabs.setCurrentIndex(i)

    def open_Vendors(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(Vendors(self.engine), "Piegādātāji")
        tabs.setCurrentIndex(i)

    def open_VendorsInvoicesUncleared(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(VendorsInvoicesUncleared(self.engine), "Neapmaksātie piegādātāju rēķini")
        tabs.setCurrentIndex(i)

    def open_VendorsInvoicesCleared(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(VendorsInvoicesCleared(self.engine), "Apmaksātie piegādātāju rēķini")
        tabs.setCurrentIndex(i)

    def open_VendorsPayments(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(VendorsPayments(self.engine), "Piegādātāju maksājumi")
        tabs.setCurrentIndex(i)

    def open_VendorsCreditnotes(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(VendorsCreditnotes(self.engine), "Piegādātāju kredītrēķini")
        tabs.setCurrentIndex(i)

    def open_CashFlowReport(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(CashFlowReport(self.engine), "Naudas plūsma")
        tabs.setCurrentIndex(i)

    def open_CashFlowDefinition(self):
        tabs = self.ui.tabWidget
        i = tabs.addTab(CashFlowDefinition(self.engine), "Naudas plūsmas definēšana")
        tabs.setCurrentIndex(i)


if __name__ == "__main__":

    app = CashFlow(sys.argv)
    app.exec()