from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class SleekWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sleek BPM Logger")
        self.setFixedSize(400, 300)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        self.title = QLabel("Welcome to Your BPM Logger")
        self.title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")

        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Enter your age")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.age_input)

        self.start_button = QPushButton("Start Logging")
        self.start_button.setFixedHeight(40)

        layout.addWidget(self.title)
        layout.addLayout(input_layout)
        layout.addWidget(self.start_button)
        layout.addStretch()

        self.setLayout(layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #2c3e50, stop:1 #4ca1af);
                color: white;
                border-radius: 15px;
            }
            QLabel {
                color: #ecf0f1;
            }
            QLineEdit {
                border: 2px solid #2980b9;
                border-radius: 10px;
                padding: 8px;
                background-color: #34495e;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1abc9c;
                background-color: #2c3e50;
            }
            QPushButton {
                background-color: #1abc9c;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
            QPushButton:pressed {
                background-color: #0e6655;
            }
        """)

if __name__ == "__main__":
    app = QApplication([])
    window = SleekWindow()
    window.show()
    app.exec()
