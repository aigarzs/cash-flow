from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

app = QApplication([])


class PopupView(QWidget):
    def __init__(self, parent=None):
        super(PopupView, self).__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup)
        # self.move(QCursor.pos())
        self.show()


class ItemDelegate(QItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        return QTextEdit(parent)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class Model(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self)
        self.items = [[1, 'one', 'ONE'], [2, 'two', 'TWO'], [3, 'three', 'THREE']]

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def rowCount(self, parent=QModelIndex()):
        return 3

    def columnCount(self, parent=QModelIndex()):
        return 3

    def data(self, index, role):
        if not index.isValid():
            return

        if role in [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]:
            return self.items[index.row()][index.column()]


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.clipboard = QApplication.clipboard()
        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        vbox = QVBoxLayout()
        mainWidget.setLayout(vbox)

        view = QTableView(self)
        view.setModel(Model())
        view.setItemDelegate(ItemDelegate(view))
        vbox.addWidget(view)


view = MainWindow()
view.show()
app.exec()
