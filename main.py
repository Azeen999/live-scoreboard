import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.views.setup_wizard import SetupWizard
from src.app.application import ScoreboardApp

DARK_QSS = """
    QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: 13px;
    }
    QGroupBox {
        border: 1px solid #45475a;
        border-radius: 6px;
        margin-top: 8px;
        padding-top: 14px;
        font-weight: bold;
        color: #cdd6f4;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
    }
    QPushButton {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 6px 14px;
        color: #cdd6f4;
    }
    QPushButton:hover {
        background-color: #45475a;
    }
    QPushButton:pressed {
        background-color: #585b70;
    }
    QPushButton:disabled {
        background-color: #1e1e2e;
        color: #585b70;
    }
    QLineEdit {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 6px 10px;
        color: #cdd6f4;
    }
    QLineEdit:focus {
        border-color: #89b4fa;
    }
    QComboBox {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 4px 8px;
        color: #cdd6f4;
    }
    QComboBox:hover {
        border-color: #89b4fa;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #313244;
        border: 1px solid #45475a;
        color: #cdd6f4;
        selection-background-color: #45475a;
    }
    QListWidget {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 6px;
        color: #cdd6f4;
        outline: none;
    }
    QListWidget::item {
        padding: 8px 12px;
    }
    QListWidget::item:selected {
        background-color: #45475a;
        border-radius: 4px;
    }
    QListWidget::item:hover {
        background-color: #36384a;
    }
    QStatusBar {
        background-color: #181825;
        color: #a6adc8;
        border-top: 1px solid #45475a;
    }
    QLabel {
        background: transparent;
    }
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("粗趣计分")
    app.setOrganizationName("CuxiScoreboard")

    wizard = SetupWizard()
    wizard.setStyleSheet(DARK_QSS)
    if wizard.exec() != SetupWizard.DialogCode.Accepted:
        sys.exit(0)

    scoreboard = ScoreboardApp(
        sport_id=wizard.selected_sport_id,
        template_id=wizard.selected_template_id,
    )
    scoreboard.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
