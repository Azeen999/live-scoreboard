from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QPushButton, QStackedWidget,
                               QWidget, QComboBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QSize
import os

from src.config.sports import SPORTS
from src.utils.resource_path import get_resource_path, list_resource_dirs


class SetupWizard(QDialog):
    """Startup wizard: select sport → select template → confirm."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("粗趣计分 - 新建比赛")
        self.setFixedSize(480, 420)
        self._selected_sport_id = "ultimate_frisbee"
        self._selected_template_id = "default"

        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        # Step indicator
        self._step_label = QLabel("步骤 1 / 3 : 选择比赛类型")
        self._step_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 12px; color: #888;"
        )
        layout.addWidget(self._step_label)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.addWidget(self._create_sport_page())
        self._stack.addWidget(self._create_template_page())
        self._stack.addWidget(self._create_confirm_page())
        layout.addWidget(self._stack, 1)

        # Navigation buttons
        nav = QHBoxLayout()
        nav.setContentsMargins(12, 12, 12, 12)
        self._btn_back = QPushButton("上一步")
        self._btn_back.setMinimumHeight(36)
        self._btn_back.setVisible(False)
        self._btn_next = QPushButton("下一步")
        self._btn_next.setMinimumHeight(36)
        self._btn_start = QPushButton("开始比赛")
        self._btn_start.setMinimumHeight(36)
        self._btn_start.setVisible(False)
        self._btn_start.setStyleSheet(
            "QPushButton { background-color: #00e676; color: #000; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { background-color: #00c853; }"
        )
        nav.addWidget(self._btn_back)
        nav.addStretch()
        nav.addWidget(self._btn_next)
        nav.addWidget(self._btn_start)
        layout.addLayout(nav)

        self._btn_back.clicked.connect(self._go_back)
        self._btn_next.clicked.connect(self._go_next)
        self._btn_start.clicked.connect(self.accept)

        self._current_step = 0
        self._update_step_ui()

    def _create_sport_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        self._sport_list = QListWidget()
        self._sport_list.setIconSize(QSize(40, 40))
        self._sport_list.setSpacing(4)
        self._sport_list.setMinimumHeight(200)

        sport_icons = {
            "ultimate_frisbee": "F",
            "badminton": "B",
            "pickleball": "P",
        }

        for sid, cfg in SPORTS.items():
            item = QListWidgetItem(f"{sport_icons.get(sid, '🏆')}  {cfg.name_zh}")
            item.setData(Qt.ItemDataRole.UserRole, sid)
            item.setSizeHint(QSize(0, 48))
            font = item.font()
            font.setPointSize(14)
            item.setFont(font)
            self._sport_list.addItem(item)

        self._sport_list.setCurrentRow(0)
        self._sport_list.currentItemChanged.connect(self._on_sport_selected)

        info_layout = QHBoxLayout()
        self._sport_info_label = QLabel("极限飞盘 | 2个半场 | 倒计时20分钟 | 15分制 | 追踪犯规")
        self._sport_info_label.setStyleSheet("color: #aaa; font-size: 12px; padding: 8px;")
        info_layout.addWidget(self._sport_info_label)
        info_layout.addStretch()

        layout.addWidget(QLabel("请选择比赛类型:"))
        layout.addWidget(self._sport_list)
        layout.addLayout(info_layout)
        self._update_sport_info(0)
        return page

    def _create_template_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        self._template_list = QListWidget()
        self._template_list.setSpacing(4)
        self._scan_templates_into_list()

        layout.addWidget(QLabel("请选择计分板模板:"))
        layout.addWidget(self._template_list)

        self._template_info = QLabel("")
        self._template_info.setStyleSheet("color: #aaa; font-size: 12px; padding: 8px;")
        layout.addWidget(self._template_info)

        self._template_list.currentItemChanged.connect(self._on_template_selected)
        if self._template_list.count() > 0:
            self._template_list.setCurrentRow(0)
        return page

    def _create_confirm_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("确认比赛设置")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 16px;")
        layout.addWidget(title)

        self._confirm_sport = QLabel()
        self._confirm_sport.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._confirm_sport.setStyleSheet("font-size: 14px; margin: 4px;")
        layout.addWidget(self._confirm_sport)

        self._confirm_template = QLabel()
        self._confirm_template.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._confirm_template.setStyleSheet("font-size: 14px; margin: 4px; color: #aaa;")
        layout.addWidget(self._confirm_template)

        hint = QLabel('点击「开始比赛」后将打开控制面板和记分板两个窗口')
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #666; margin-top: 12px;")
        layout.addWidget(hint)

        layout.addStretch()
        return page

    def _scan_templates_into_list(self):
        names = list_resource_dirs("templates")
        for name in names:
            p = get_resource_path(os.path.join("templates", name))
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "template.json")):
                item = QListWidgetItem(f"  {name}")
                item.setData(Qt.ItemDataRole.UserRole, name)
                item.setSizeHint(QSize(0, 40))
                self._template_list.addItem(item)
        if self._template_list.count() == 0:
            item = QListWidgetItem("默认模板")
            item.setData(Qt.ItemDataRole.UserRole, "default")
            item.setSizeHint(QSize(0, 40))
            self._template_list.addItem(item)

    def _on_sport_selected(self, current, previous):
        if current:
            self._selected_sport_id = current.data(Qt.ItemDataRole.UserRole)
            idx = self._sport_list.row(current)
            self._update_sport_info(idx)

    def _update_sport_info(self, idx: int):
        sports_list = list(SPORTS.values())
        if 0 <= idx < len(sports_list):
            cfg = sports_list[idx]
            mode = "倒计时" if cfg.timer_mode == "countdown" else "正计时"
            fouls = "追踪犯规" if cfg.track_fouls else "无犯规统计"
            max_s = f"{cfg.max_score}分制" if cfg.max_score else "无上限"
            periods = f"{cfg.periods_count}个{cfg.period_labels[0] if cfg.period_labels else '节'}"
            dur = f"{cfg.period_duration_seconds // 60}分钟" if cfg.period_duration_seconds > 0 else "不限时"
            self._sport_info_label.setText(
                f"{cfg.name_zh} | {periods} | {mode}{dur} | {max_s} | {fouls}"
            )

    def _on_template_selected(self, current, previous):
        if current:
            self._selected_template_id = current.data(Qt.ItemDataRole.UserRole)
            self._template_info.setText(f"已选择: {current.text()}")

    def _go_next(self):
        if self._current_step < 2:
            self._current_step += 1
            self._update_step_ui()

    def _go_back(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step_ui()

    def _update_step_ui(self):
        steps = [
            "步骤 1 / 3 : 选择比赛类型",
            "步骤 2 / 3 : 选择计分板模板",
            "步骤 3 / 3 : 确认设置",
        ]
        self._step_label.setText(steps[self._current_step])
        self._stack.setCurrentIndex(self._current_step)
        self._btn_back.setVisible(self._current_step > 0)
        self._btn_next.setVisible(self._current_step < 2)
        self._btn_start.setVisible(self._current_step == 2)

        if self._current_step == 2:
            cfg = SPORTS.get(self._selected_sport_id)
            self._confirm_sport.setText(f"比赛类型: {cfg.name_zh if cfg else self._selected_sport_id}")
            self._confirm_template.setText(f"计分板模板: {self._selected_template_id}")

    @property
    def selected_sport_id(self) -> str:
        return self._selected_sport_id

    @property
    def selected_template_id(self) -> str:
        return self._selected_template_id
