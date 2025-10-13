import sys
import csv
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt

class CSVFileHandler(logging.Handler):
    """Custom logging handler that writes logs in CSV format."""
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

        # Write header only once (if file empty)
        try:
            with open(self.filename, "x", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "level", "name", "message"])
        except FileExistsError:
            pass  # file already exists, no need to rewrite header

    def emit(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        name = record.name
        message = record.getMessage()

        with open(self.filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, level, name, message])

class QTextEditHandler(logging.Handler):
    """A logging handler that writes log messages to a QTextEdit."""
    def __init__(self, text_widget: QTextEdit):
        super().__init__()
        self.widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # Ensure GUI updates happen in the main thread
        self.widget.append(msg)
        self.widget.verticalScrollBar().setValue(
            self.widget.verticalScrollBar().maximum()
        )


def get_logger(name=None):
    if not isinstance(name, str):
        name = type(name).__name__
    logger = logging.getLogger(name)
    from cash_flow.util.Settings import logLevel
    logger.setLevel(logLevel)
    logger.handlers.clear()
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    csv_handler = CSVFileHandler("../../log/app_log.csv")
    logger.addHandler(csv_handler)
    return logger


log_sql = get_logger("SQL")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Logging Example")

        # Layout and widgets
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.button_info = QPushButton("Log Info")
        self.button_warn = QPushButton("Log Warning")
        self.button_error = QPushButton("Log Error")
        layout.addWidget(self.button_info)
        layout.addWidget(self.button_warn)
        layout.addWidget(self.button_error)

        self.setLayout(layout)

        # Setup logging
        self.setup_logging()

        # Connect buttons
        self.button_info.clicked.connect(lambda: logging.info("This is an info message"))
        self.button_warn.clicked.connect(lambda: logging.warning("This is a warning"))
        self.button_error.clicked.connect(lambda: logging.error("This is an error!"))

    def setup_logging(self):
        logger = get_logger()

        # QTextEdit handler
        text_handler = QTextEditHandler(self.text_edit)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        text_handler.setFormatter(formatter)
        logger.addHandler(text_handler)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(500, 400)
    window.show()
    sys.exit(app.exec())
