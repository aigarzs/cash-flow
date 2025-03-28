from PyQt6.QtWidgets import QApplication, QTableView
from PyQt6.QtCore import QAbstractTableModel, Qt
import pandas as pd

class PandasModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self.df = df

    def rowCount(self, parent=None):
        return self.df.shape[0]

    def columnCount(self, parent=None):
        return self.df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.df.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.df.columns[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(self.df.index[section])  # Display index values as row headers
        return None

def select_row_by_id(view, model, df, id_value):
    try:
        row_index = df.index.get_loc(id_value)  # Get the position of the index value
        view.selectRow(row_index)  # Select the corresponding row
    except KeyError:
        print(f"ID {id_value} not found in DataFrame index")

# Create DataFrame with 'id' as the index
df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]}, index=[5, 10, 15])
df.index.name = "id"  # Naming the index

app = QApplication([])

# Create TableView and Model
model = PandasModel(df)
view = QTableView()
view.setModel(model)
view.show()

# Select row where index (id) == 10
select_row_by_id(view, model, df, 10)

app.exec()
