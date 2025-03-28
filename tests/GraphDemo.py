import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
import pyqtgraph as pg


def generate_dummy_data():
    dates = pd.date_range(start="2024-01-01", periods=30, freq='D')
    amounts = np.random.randint(-500, 500, size=30)
    df = pd.DataFrame({'Date': dates, 'Amount': amounts})
    df['Balance'] = df['Amount'].cumsum()
    return df


class BankBalancePlot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bank Account Balance Trend")
        self.setGeometry(100, 100, 800, 500)

        self.df = generate_dummy_data()
        self.dates_numeric = [i for i in range(len(self.df))]  # Convert dates to indices for x-axis

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.scatter_plot = pg.ScatterPlotItem()
        self.plot_widget.addItem(self.scatter_plot)

        self.plot_data()

        self.scatter_plot.sigClicked.connect(self.on_plot_clicked)

    def plot_data(self):
        self.curve = self.plot_widget.plot(self.dates_numeric, self.df['Balance'].values,
                                           pen=pg.mkPen(color='b', width=2))
        self.scatter_plot.setData(self.dates_numeric, self.df['Balance'].values, symbol='o', symbolSize=8,
                                  symbolBrush='r')
        self.plot_widget.setTitle("Daily Running Balance")
        self.plot_widget.setLabel('left', 'Balance ($)')
        self.plot_widget.setLabel('bottom', 'Days')

    def on_plot_clicked(self, scatter, points):
        if points:
            index = int(points[0].index())
            balance = self.df.iloc[index]['Balance']
            date = self.df.iloc[index]['Date'].strftime('%Y-%m-%d')
            QMessageBox.information(self, "Daily Balance", f"Date: {date}\nBalance: ${balance}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BankBalancePlot()
    window.show()
    sys.exit(app.exec())