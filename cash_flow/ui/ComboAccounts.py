import sys

from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QTableView, QVBoxLayout, QWidget, QAbstractItemView
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QStringListModel, QModelIndex, QVariant
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from cash_flow.database.AEngine import engine
from cash_flow.database.Model import Account
from cash_flow.ui.AWidgets import ATableModel_set


# Custom Table Model for Multi-Column ComboBox
class ComboTableModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0])

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            row, col = index.row(), index.column()
            return self._data[row][col]
        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        headers = ["V/G konts", "Nosaukums"]
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return headers[section]
        return QVariant()




# Custom ComboBox with Multi-Column Dropdown
class ComboAccounts(QComboBox):
    def __init__(self, engine, parent=None):
        super().__init__(parent)

        stmt = select(Account.code, Account.name).order_by(Account.code)
        with Session(engine) as session:
            self.data = session.execute(stmt).fetchall()

        # Set up a table view as a popup for multi-column display
        self.table_view = QTableView(self)
        self.table_view.setModel(ComboTableModel(self.data, self))
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.verticalHeader().hide()
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setWindowFlags(Qt.WindowType.Popup)

        # Model to hold just the first column data, for QComboBox's displayed text
        self.display_model = QStringListModel([row[0] for row in self.data], self)
        self.setModel(self.display_model)

        # Connect selection change to update combo box text
        self.table_view.clicked.connect(self.handle_selection)

    def showPopup(self):
        # Get the screen geometry of the screen where the widget is displayed
        screen = self.screen()  # Obtain the screen of the current widget
        if screen is not None:
            screen_geometry = screen.availableGeometry()
        else:
            # Fallback to primary screen in case no screen is detected (this is rare)
            screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())

        # Set the initial geometry of the popup below the combo box
        popup_width = max(self.width(), 300)
        popup_height = 200
        combo_box_position = self.mapToGlobal(self.geometry().bottomLeft())

        # Adjust position if it goes beyond the screen
        if combo_box_position.x() + popup_width > screen_geometry.right():
            combo_box_position.setX(screen_geometry.right() - popup_width)
        if combo_box_position.y() + popup_height > screen_geometry.bottom():
            combo_box_position.setY(screen_geometry.bottom() - popup_height)

        # Set geometry for the table view
        self.table_view.setGeometry(combo_box_position.x(), combo_box_position.y(), popup_width, popup_height)
        self.table_view.show()

    def hidePopup(self):
        self.table_view.hide()

    def handle_selection(self, index):
        row = index.row()
        # Set the selected row in the display model to update combo box text
        self.setCurrentIndex(row)  # This selects the item in the combo box's display model
        self.hidePopup()


# Main Application
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Column ComboBox Example")
        layout = QVBoxLayout()

        # Add our custom multi-column combo box to the layout
        self.comboBox = ComboAccounts(engine, self)
        layout.addWidget(self.comboBox)

        self.setLayout(layout)


if __name__ == "__main__":
    # Run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
