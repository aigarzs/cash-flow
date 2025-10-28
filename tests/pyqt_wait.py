import sys

from PyQt6.QtCore import QThread, QObject, pyqtSignal, QCoreApplication


class MyExample:
    def requery(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_requery_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        print(f"Requery start")

        self.thread.start()


    def on_requery_finished(self, item):
        print(f"on_requery_finished")

        print(f"Requery finished. {item}")

class Worker(QObject):
    finished = pyqtSignal(int)

    def run(self):
        print("Worker started")
        print("Worker finished")
        self.finished.emit(12)


if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    example = MyExample()
    example.requery()

    # Start the event loop — this allows signals and slots to work
    sys.exit(app.exec())


    # Now that the event loop has exited, the thread should be done
    example.thread.wait()
    print("Waiting finished")




