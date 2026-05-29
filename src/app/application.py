import os

from PySide6.QtCore import QTimer

from src.models.game_state import GameState
from src.views.control_panel import ControlPanel
from src.views.scoreboard_window import ScoreboardWindow
from src.config.sports import SPORTS
from src.utils.resource_path import get_resource_path

# Dark theme QSS for control panel only — must not affect the scoreboard window
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
    QPushButton:hover { background-color: #45475a; }
    QPushButton:pressed { background-color: #585b70; }
    QPushButton:disabled { background-color: #1e1e2e; color: #585b70; }
    QLineEdit {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 6px 10px;
        color: #cdd6f4;
    }
    QLineEdit:focus { border-color: #89b4fa; }
    QComboBox {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 4px;
        padding: 4px 8px;
        color: #cdd6f4;
    }
    QComboBox:hover { border-color: #89b4fa; }
    QComboBox::drop-down { border: none; }
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
    QListWidget::item { padding: 8px 12px; }
    QListWidget::item:selected { background-color: #45475a; border-radius: 4px; }
    QListWidget::item:hover { background-color: #36384a; }
    QStatusBar {
        background-color: #181825;
        color: #a6adc8;
        border-top: 1px solid #45475a;
    }
    QLabel { background: transparent; }
"""


class ScoreboardApp:
    def __init__(self, sport_id: str = "ultimate_frisbee", template_id: str = "default"):
        self.game_state = GameState()
        self.game_state.set_sport(sport_id)
        self.game_state.set_template(template_id)

        self._timer = QTimer()
        self._timer.timeout.connect(self.game_state.tick)
        self._timer.start(1000)

        self.control_panel = ControlPanel(self.game_state)
        self.control_panel.setStyleSheet(DARK_QSS)

        self.scoreboard_window = ScoreboardWindow(self.game_state)
        self.control_panel.set_scoreboard_window(self.scoreboard_window)

        self._load_initial_template(template_id)

        self.game_state.template_changed.connect(self._on_template_changed)

    def _load_initial_template(self, template_id: str):
        template_dir = get_resource_path(os.path.join("templates", template_id))
        if os.path.isdir(template_dir):
            self.scoreboard_window.load_template(template_dir)

    def _on_template_changed(self, template_id: str):
        template_dir = get_resource_path(os.path.join("templates", template_id))
        if os.path.isdir(template_dir):
            self.scoreboard_window.load_template(template_dir)

    def show(self):
        self.scoreboard_window.show()
        self.control_panel.show()
