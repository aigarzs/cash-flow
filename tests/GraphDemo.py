import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QFileDialog
)
from PyQt6.QtGui import QPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import mplcursors


class CashflowChart(QWidget):
    def __init__(self, final_df):
        super().__init__()
        self.final_df = final_df
        self.dark_theme = self.detect_dark_mode()
        self.bar_cursor = None
        self.line_cursor = None
        self.annotations = []
        self.initUI()

    def detect_dark_mode(self):
        palette = self.palette()
        bg_color = palette.color(QPalette.ColorRole.Window)
        r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()
        luminance = 0.2126 * r/255 + 0.7152 * g/255 + 0.0722 * b/255
        return luminance < 0.5

    def initUI(self):
        layout = QVBoxLayout(self)

        self.figure, self.ax = plt.subplots(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Add export button
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export to JPG")
        self.export_btn.clicked.connect(self.save_figure_as_jpg)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

        # Connect to hide tooltips
        self.canvas.mpl_connect("button_press_event", self.hide_tooltips)

        self.plot_cashflow()

    def plot_cashflow(self):
        df = self.final_df.copy()
        self.ax.clear()
        self.annotations = []

        periods = df.columns
        x = range(len(periods))

        # Theme settings
        if self.dark_theme:
            bg_color = "#222222"
            fg_color = "white"
            grid_color = "#555555"
        else:
            bg_color = "white"
            fg_color = "black"
            grid_color = "#cccccc"

        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        self.ax.tick_params(colors=fg_color)
        self.ax.yaxis.label.set_color(fg_color)
        self.ax.xaxis.label.set_color(fg_color)
        self.ax.title.set_color(fg_color)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(fg_color)

        self.ax.grid(True, color=grid_color)

        bottom = [0] * len(periods)
        colors = plt.cm.tab20.colors
        bar_patch_map = {}

        for i, account in enumerate(df.index):
            values = df.loc[account].values
            bars = self.ax.bar(
                x,
                values,
                bottom=bottom,
                label=account,
                color=colors[i % len(colors)]
            )
            for idx, bar in enumerate(bars):
                bar_patch_map[bar] = {
                    "account": account,
                    "val": values[idx],
                    "period": periods[idx]
                }
            bottom = [b + v for b, v in zip(bottom, values)]

        net_cashflow = df.sum(axis=0).values
        line1, = self.ax.plot(x, net_cashflow, color='black', label='Net Cashflow', marker='o', linewidth=2)
        cumulative_balance = net_cashflow.cumsum()
        line2, = self.ax.plot(x, cumulative_balance, color='blue', label='Balance', linestyle='--', marker='x', linewidth=2)

        self.ax.set_xticks(x)
        self.ax.set_xticklabels([p.strftime('%Y-%m-%d') for p in periods], rotation=45, ha='right')
        self.ax.set_ylabel("Amount")
        self.ax.set_title("Cash Flow by Account and Period")
        self.ax.legend()

        # Remove old cursors if they exist
        if self.bar_cursor:
            self.bar_cursor.remove()
        if self.line_cursor:
            self.line_cursor.remove()

        # Bar tooltips
        self.bar_cursor = mplcursors.cursor(bar_patch_map.keys(), hover=True)

        @self.bar_cursor.connect("add")
        def on_add_bar(sel):
            info = bar_patch_map.get(sel.artist)
            if info:
                sel.annotation.set_text(
                    f"{info['account']}\n{info['period'].strftime('%Y-%m-%d')}\n{info['val']:,.2f}"
                )
                sel.annotation.get_bbox_patch().set_facecolor(sel.artist.get_facecolor())
                sel.annotation.get_bbox_patch().set_alpha(0.7)
                self.annotations.append(sel.annotation)

        # Line tooltips
        self.line_cursor = mplcursors.cursor([line1, line2], hover=True)

        @self.line_cursor.connect("add")
        def on_add_line(sel):
            label = line1.get_label() if sel.artist == line1 else line2.get_label()
            period = periods[int(sel.index)]
            y = sel.target[1]
            sel.annotation.set_text(f"{label}\n{period.strftime('%Y-%m-%d')}\n{y:,.2f}")
            sel.annotation.get_bbox_patch().set_facecolor((0.2, 0.2, 0.2, 0.8) if self.dark_theme else (1, 1, 1, 0.8))
            self.annotations.append(sel.annotation)

        self.canvas.draw()

    def hide_tooltips(self, event):
        for ann in self.annotations:
            ann.set_visible(False)
        self.annotations.clear()
        self.canvas.draw_idle()

    def save_figure_as_jpg(self):
        current_theme = self.dark_theme
        self.dark_theme = False

        # Remove tooltips and cursors
        if self.bar_cursor:
            self.bar_cursor.remove()
            self.bar_cursor = None
        if self.line_cursor:
            self.line_cursor.remove()
            self.line_cursor = None
        self.annotations.clear()

        self.plot_cashflow()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "cashflow_export.jpg", "JPEG Files (*.jpg);;All Files (*)"
        )
        if file_path:
            self.figure.savefig(file_path, facecolor='white', bbox_inches='tight', dpi=300)
            print(f"Graph exported to {file_path}")

        self.dark_theme = current_theme
        self.plot_cashflow()


class MainWindow(QMainWindow):
    def __init__(self, final_df):
        super().__init__()
        self.setWindowTitle("Cash Flow Viewer")
        self.setCentralWidget(CashflowChart(final_df))
        self.resize(1000, 600)


if __name__ == '__main__':
    accounts = ['Sales', 'Marketing', 'Ops']
    dates = pd.date_range('2025-01-31', periods=6, freq='M')
    data = {
        account: [1000 * (i + 1) * (-1 if i % 2 else 1) for i in range(len(dates))]
        for account in accounts
    }
    final_df = pd.DataFrame(data, index=dates).T

    app = QApplication(sys.argv)
    window = MainWindow(final_df)
    window.show()
    sys.exit(app.exec())
