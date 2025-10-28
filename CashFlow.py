
import sys

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, QToolBox, QPushButton, \
    QTabWidget

from cash_flow.database.AEngine import create_engine_db
from cash_flow.ui.Budget import Budget
from cash_flow.ui.CashFlowDefinition import CashFlowDefinition
from cash_flow.ui.CashFlowReport import CashFlowReport
from cash_flow.ui.Customers import Customers
from cash_flow.ui.CustomersInvoices import CustomersInvoices
from cash_flow.ui.CustomersPayments import CustomersPayments
from cash_flow.ui.Vendors import Vendors
from cash_flow.ui.VendorsInvoices import VendorsInvoices
from cash_flow.ui.VendorsPayments import VendorsPayments
from cash_flow.util.log import get_logger
from cash_flow.util.Settings import *


class CashFlowApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.logger = get_logger("CashFlowApp")
        self.init_settings()
        self.init_database()
        self.init_ui()
        self.translate_ui()
        self.setup_actions()
        self.mainWindow.show()

    def init_settings(self):
        self.logger.info("******** logging settings *******")
        self.logger.info(f"Log level={logLevel}")
        self.logger.info("******** pandas settings ********")
        self.logger.info(f"pd.options.mode.copy_on_write={pd.options.mode.copy_on_write}")
        self.logger.info("******** alchemy settings ********")
        self.logger.info(f"Engine echo={engine_echo}")
        self.logger.info("************ EOF settings *****************")

    def init_database(self):
        self.engine = create_engine_db()

    def init_ui(self):
        self.mainWindow = QMainWindow()
        self.mainWindow.resize(800, 600)
        centralwidget = QWidget(parent=self.mainWindow)
        vbox = QVBoxLayout(centralwidget)

        splitter = QSplitter(parent=centralwidget)
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)

        self.toolBox = QToolBox(parent=splitter)
        self.toolBox.setMinimumSize(QtCore.QSize(100, 0))
        self.toolBox.setMaximumSize(QtCore.QSize(200, 16777215))
        self.toolBox.setBaseSize(QtCore.QSize(200, 0))

        self.page_customers = QWidget()
        self.page_customers.setGeometry(QtCore.QRect(0, 0, 200, 419))
        layout_customers = QVBoxLayout(self.page_customers)
        self.btn_Customers = QPushButton(parent=self.page_customers)
        layout_customers.addWidget(self.btn_Customers)
        self.btn_CustomersInvoices = QPushButton(parent=self.page_customers)
        layout_customers.addWidget(self.btn_CustomersInvoices)
        self.btn_CustomersPayments = QPushButton(parent=self.page_customers)
        layout_customers.addWidget(self.btn_CustomersPayments)

        self.page_vendors = QWidget()
        self.page_vendors.setGeometry(QtCore.QRect(0, 0, 148, 102))
        layout_vendors = QVBoxLayout(self.page_vendors)
        self.btn_Vendors = QPushButton(parent=self.page_vendors)
        layout_vendors.addWidget(self.btn_Vendors)
        self.btn_VendorsInvoices = QPushButton(parent=self.page_vendors)
        layout_vendors.addWidget(self.btn_VendorsInvoices)
        self.btn_VendorsPayments = QPushButton(parent=self.page_vendors)
        layout_vendors.addWidget(self.btn_VendorsPayments)

        self.page_cashflow = QWidget()
        self.page_cashflow.setGeometry(QtCore.QRect(0, 0, 200, 419))
        layout_cashflow = QVBoxLayout(self.page_cashflow)
        self.btn_CashFlowDefinition = QPushButton(parent=self.page_cashflow)
        layout_cashflow.addWidget(self.btn_CashFlowDefinition)
        self.btn_CashFlowReport = QPushButton(parent=self.page_cashflow)
        layout_cashflow.addWidget(self.btn_CashFlowReport)
        self.btn_Budget = QPushButton(parent=self.page_cashflow)
        layout_cashflow.addWidget(self.btn_Budget)

        self.page_settings = QWidget()
        self.page_settings.setGeometry(QtCore.QRect(0, 0, 98, 132))
        layout_settings = QVBoxLayout(self.page_settings)
        self.pushButton = QPushButton(parent=self.page_settings)
        layout_settings.addWidget(self.pushButton)
        self.pushButton_3 = QPushButton(parent=self.page_settings)
        layout_settings.addWidget(self.pushButton_3)
        self.pushButton_2 = QPushButton(parent=self.page_settings)
        layout_settings.addWidget(self.pushButton_2)
        self.btn_Accounts = QPushButton(parent=self.page_settings)
        layout_settings.addWidget(self.btn_Accounts)

        self.toolBox.addItem(self.page_customers, "")
        self.toolBox.addItem(self.page_vendors, "")
        self.toolBox.addItem(self.page_cashflow, "")
        self.toolBox.addItem(self.page_settings, "")

        self.tabWidget = QTabWidget(parent=splitter)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
        self.tabWidget.setTabsClosable(True)

        vbox.addWidget(splitter)
        self.mainWindow.setCentralWidget(centralwidget)

        self.menubar = QtWidgets.QMenuBar(parent=self.mainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.mainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=self.mainWindow)
        self.mainWindow.setStatusBar(self.statusbar)

        self.toolBox.setCurrentIndex(2)
        self.tabWidget.setCurrentIndex(-1)

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.mainWindow.setWindowTitle(_translate("MainWindow", "Naudas plūsma"))
        self.btn_Customers.setText(_translate("MainWindow", "Klienti"))
        self.btn_CustomersInvoices.setText(_translate("MainWindow", "Klientu rēķini"))
        self.btn_CustomersPayments.setText(_translate("MainWindow", "Klientu maksājumi"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_customers), _translate("MainWindow", "Ienākumi"))
        self.btn_Vendors.setText(_translate("MainWindow", "Piegādātāji"))
        self.btn_VendorsInvoices.setText(_translate("MainWindow", "Piegādātāju rēķini"))
        self.btn_VendorsPayments.setText(_translate("MainWindow", "Piegādātāju maksājumi"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_vendors), _translate("MainWindow", "Maksājumi"))
        self.btn_CashFlowDefinition.setText(_translate("MainWindow", "Struktūras definēšana"))
        self.btn_CashFlowReport.setText(_translate("MainWindow", "Naudas plūsmas atskaite"))
        self.btn_Budget.setText(_translate("MainWindow", "Budžets"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_cashflow), _translate("MainWindow", "Naudas plūsma"))
        self.pushButton.setText(_translate("MainWindow", "Datubāze"))
        self.pushButton_3.setText(_translate("MainWindow", "Datu avoti"))
        self.pushButton_2.setText(_translate("MainWindow", "Lietotāji"))
        self.btn_Accounts.setText(_translate("MainWindow", "Kontu plāns"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_settings), _translate("MainWindow", "Uzstādījumi"))

    def setup_actions(self):
        self.tabWidget.tabCloseRequested.connect(lambda index: self.tabWidget.removeTab(index))

        self.btn_CustomersInvoices.clicked.connect(lambda: self.open_Form(CustomersInvoices(self.engine), "Klientu rēķini"))
        self.btn_CustomersPayments.clicked.connect(lambda: self.open_Form(CustomersPayments(self.engine), "Klientu maksājumi"))
        self.btn_Customers.clicked.connect(lambda: self.open_Form(Customers(self.engine), "Klienti"))
        self.btn_Vendors.clicked.connect(lambda: self.open_Form(Vendors(self.engine), "Piegādātāji"))
        self.btn_VendorsInvoices.clicked.connect(lambda: self.open_Form(VendorsInvoices(self.engine), "Piegādātāju rēķini"))
        self.btn_VendorsPayments.clicked.connect(lambda: self.open_Form(VendorsPayments(self.engine), "Piegādātāju maksājumi"))
        self.btn_CashFlowReport.clicked.connect(lambda: self.open_Form(CashFlowReport(self.engine), "Naudas plūsma"))
        self.btn_CashFlowDefinition.clicked.connect(lambda: self.open_Form(CashFlowDefinition(self.engine), "Naudas plūsmas definēšana"))
        self.btn_Budget.clicked.connect(lambda: self.open_Form(Budget(self.engine), "Budžets"))

    def open_Form(self, form, name):
        i = self.tabWidget.addTab(form, name)
        self.tabWidget.setCurrentIndex(i)


if __name__ == '__main__':
    app = CashFlowApp(sys.argv)
    sys.exit(app.exec())
