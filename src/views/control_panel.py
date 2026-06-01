from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QComboBox,
                               QVBoxLayout, QHBoxLayout, QPushButton,
                               QLineEdit, QGroupBox, QSpinBox, QStatusBar,
                               QGridLayout)
from PySide6.QtCore import Qt
import os

from src.models.game_state import GameState
from src.config.sports import SPORTS
from src.utils.resource_path import get_resource_path, list_resource_dirs
from src.views.style_editor import StyleEditor


class ControlPanel(QMainWindow):
    def __init__(self, game_state: GameState):
        super().__init__()
        self._gs = game_state
        self._scoreboard_window = None
        self.setWindowTitle("控制面板 - 粗趣计分")
        self.resize(620, 340)
        self.setMinimumSize(520, 300)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(8, 6, 8, 6)

        # === Row 0: Sport + Template ===
        top = QHBoxLayout()
        top.setSpacing(4)
        top.addWidget(QLabel("运动:"))
        self._sport_combo = QComboBox()
        self._sport_combo.setMinimumHeight(24)
        for sid, cfg in SPORTS.items():
            self._sport_combo.addItem(cfg.name_zh, sid)
        top.addWidget(self._sport_combo)
        top.addSpacing(8)
        top.addWidget(QLabel("模板:"))
        self._template_combo = QComboBox()
        self._template_combo.setMinimumHeight(24)
        self._scan_templates()
        top.addWidget(self._template_combo)
        top.addStretch()
        main_layout.addLayout(top)

        # === Row 1: Team A | Timer | Team B ===
        teams_timer = QHBoxLayout()
        teams_timer.setSpacing(4)

        # Team A
        grp_a = QGroupBox("左队")
        la = QVBoxLayout(grp_a)
        la.setSpacing(2)
        la.setContentsMargins(6, 12, 6, 6)
        self._name_a = QLineEdit(self._gs.team_a_name)
        self._name_a.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_a.setMaximumHeight(24)
        la.addWidget(self._name_a)

        self._score_a = QLabel("0")
        self._score_a.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_a_color = "#ffffff"
        self._score_a_original_color = "#ffffff"
        self._score_a.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._score_a_color};")
        self._score_a.setMaximumHeight(40)
        la.addWidget(self._score_a)

        btns_a = QHBoxLayout()
        btns_a.setSpacing(2)
        for label, delta in [("-1", -1), ("+1", 1)]:
            btn = QPushButton(label)
            btn.setFixedSize(44, 28)
            btn.clicked.connect(lambda checked, d=delta: self._gs.increment_score("A", d))
            btns_a.addWidget(btn)
        la.addLayout(btns_a)
        teams_timer.addWidget(grp_a)

        # Timer
        grp_t = QGroupBox("计时器")
        lt = QVBoxLayout(grp_t)
        lt.setSpacing(2)
        lt.setContentsMargins(6, 12, 6, 6)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(4)
        self._btn_mode = QPushButton("倒计时")
        self._btn_mode.setCheckable(True)
        self._btn_mode.setFixedHeight(28)
        self._btn_mode.setToolTip("点击切换 倒计时/秒表")
        mode_row.addWidget(self._btn_mode)
        mode_row.addStretch()
        lt.addLayout(mode_row)

        time_row = QHBoxLayout()
        time_row.setSpacing(2)
        self._time_min = QSpinBox()
        self._time_min.setRange(0, 99)
        self._time_min.setSuffix(" 分")
        self._time_min.setFixedHeight(24)
        self._time_sec = QSpinBox()
        self._time_sec.setRange(0, 59)
        self._time_sec.setSuffix(" 秒")
        self._time_sec.setFixedHeight(24)
        time_row.addWidget(self._time_min)
        time_row.addWidget(self._time_sec)
        self._btn_set_time = QPushButton("设定")
        self._btn_set_time.setFixedHeight(24)
        self._btn_set_time.setFixedWidth(40)
        time_row.addWidget(self._btn_set_time)
        lt.addLayout(time_row)

        self._time_label = QLabel("30:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self._time_label.setMaximumHeight(30)
        lt.addWidget(self._time_label)

        tbtns = QHBoxLayout()
        tbtns.setSpacing(2)
        self._btn_start = QPushButton("开始")
        self._btn_pause = QPushButton("暂停")
        self._btn_reset_t = QPushButton("重置")
        for b in (self._btn_start, self._btn_pause, self._btn_reset_t):
            b.setFixedHeight(28)
            tbtns.addWidget(b)
        lt.addLayout(tbtns)

        self._btn_mode.clicked.connect(self._on_mode_toggle)
        self._btn_set_time.clicked.connect(self._on_set_time)
        self._btn_start.clicked.connect(self._gs.start_timer)
        self._btn_pause.clicked.connect(self._gs.pause_timer)
        self._btn_reset_t.clicked.connect(self._gs.reset_timer)
        teams_timer.addWidget(grp_t)

        # Team B
        grp_b = QGroupBox("右队")
        lb = QVBoxLayout(grp_b)
        lb.setSpacing(2)
        lb.setContentsMargins(6, 12, 6, 6)
        self._name_b = QLineEdit(self._gs.team_b_name)
        self._name_b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_b.setMaximumHeight(24)
        lb.addWidget(self._name_b)

        self._score_b = QLabel("0")
        self._score_b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_b_color = "#ffffff"
        self._score_b_original_color = "#ffffff"
        self._score_b.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._score_b_color};")
        self._score_b.setMaximumHeight(40)
        lb.addWidget(self._score_b)

        btns_b = QHBoxLayout()
        btns_b.setSpacing(2)
        for label, delta in [("-1", -1), ("+1", 1)]:
            btn = QPushButton(label)
            btn.setFixedSize(44, 28)
            btn.clicked.connect(lambda checked, d=delta: self._gs.increment_score("B", d))
            btns_b.addWidget(btn)
        lb.addLayout(btns_b)
        teams_timer.addWidget(grp_b)

        main_layout.addLayout(teams_timer, 1)

        # === Row 2: Period (left) + Action buttons 2x3 grid (right) ===
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        grp_p = QGroupBox("节次")
        lp = QHBoxLayout(grp_p)
        lp.setContentsMargins(6, 10, 6, 6)
        lp.setSpacing(4)
        self._period_combo = QComboBox()
        self._period_combo.setMinimumHeight(24)
        self._period_combo.setMinimumWidth(80)
        self._period_combo.setMaximumWidth(100)
        lp.addWidget(self._period_combo)
        bottom_row.addWidget(grp_p, 0)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(3)

        self._btn_swap = QPushButton("交换比分")
        self._btn_style = QPushButton("样式")
        self._btn_reset = QPushButton("全部重置")
        self._btn_show = QPushButton("隐藏记分板")
        self._btn_top = QPushButton("悬浮置顶")
        self._btn_center_top = QPushButton("居中显示")
        self._btn_top.setCheckable(True)
        self._btn_top.setChecked(False)

        all_btns = [
            (self._btn_swap, 0, 0), (self._btn_style, 0, 1), (self._btn_reset, 0, 2),
            (self._btn_show, 1, 0), (self._btn_top, 1, 1), (self._btn_center_top, 1, 2),
        ]
        for btn, r, c in all_btns:
            btn.setFixedHeight(30)
            btn_grid.addWidget(btn, r, c)

        bottom_row.addLayout(btn_grid, 1)
        main_layout.addLayout(bottom_row)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("就绪")

        # ---- Internal connections ----
        self._sport_combo.currentIndexChanged.connect(self._on_sport_changed)
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        self._sync_template_combo()
        self._period_combo.currentIndexChanged.connect(self._on_period_changed)
        self._name_a.editingFinished.connect(self._on_names_changed)
        self._name_b.editingFinished.connect(self._on_names_changed)

        self._btn_swap.clicked.connect(self._gs.swap_sides)
        self._btn_swap.clicked.connect(self._on_swap_colors)
        self._btn_style.clicked.connect(self._open_style_editor)
        self._btn_reset.clicked.connect(self._gs.reset_all)
        self._btn_show.clicked.connect(self._toggle_scoreboard)
        self._btn_top.clicked.connect(self._toggle_stay_on_top)
        self._btn_center_top.clicked.connect(self._on_center_top)

        # ---- GameState signal connections ----
        gs = self._gs
        gs.team_a_name_changed.connect(self._name_a.setText)
        gs.team_b_name_changed.connect(self._name_b.setText)
        gs.team_a_score_changed.connect(lambda v: self._score_a.setText(str(v)))
        gs.team_b_score_changed.connect(lambda v: self._score_b.setText(str(v)))
        gs.timer_seconds_changed.connect(self._update_timer_display)
        gs.timer_running_changed.connect(self._on_running)
        gs.period_changed.connect(self._on_state_period)
        gs.sport_changed.connect(self._on_sport_state)
        gs.overtime_changed.connect(self._on_ot)
        gs.scores_reset.connect(self._on_reset)
        gs.timer_expired.connect(self._on_timer_expired)
        gs.timer_mode_changed.connect(self._on_timer_mode_state)

        self._refresh_periods()
        self._sync_timer_mode()
        self._sync_time_spinboxes()
        self._on_reset()

    def _scan_templates(self):
        for name in list_resource_dirs("templates"):
            p = get_resource_path(os.path.join("templates", name))
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "template.json")):
                self._template_combo.addItem(name, name)
        if self._template_combo.count() == 0:
            self._template_combo.addItem("默认", "default")

    def _sync_template_combo(self):
        self._template_combo.blockSignals(True)
        for i in range(self._template_combo.count()):
            if self._template_combo.itemData(i) == self._gs.template_id:
                self._template_combo.setCurrentIndex(i)
                break
        self._template_combo.blockSignals(False)

    def _on_sport_changed(self, idx: int):
        sid = self._sport_combo.currentData()
        if sid:
            self._gs.set_sport(sid)

    def _on_sport_state(self, _):
        sid = self._gs.sport_config.sport_id
        self._sport_combo.blockSignals(True)
        for i in range(self._sport_combo.count()):
            if self._sport_combo.itemData(i) == sid:
                self._sport_combo.setCurrentIndex(i)
                break
        self._sport_combo.blockSignals(False)
        self._refresh_periods()
        self._sync_timer_mode()

    def _on_template_changed(self, idx: int):
        tid = self._template_combo.currentData()
        if tid:
            self._gs.set_template(tid)

    def _on_names_changed(self):
        a = self._name_a.text().strip()
        b = self._name_b.text().strip()
        if a:
            self._gs.set_team_a_name(a)
        if b:
            self._gs.set_team_b_name(b)

    def _refresh_periods(self):
        self._period_combo.blockSignals(True)
        self._period_combo.clear()
        for label in self._gs.sport_config.period_labels:
            self._period_combo.addItem(label)
        # Add overtime as last option
        if self._gs.sport_config.has_overtime:
            self._period_combo.addItem(self._gs.sport_config.overtime_label)
        # Select current period, or overtime if active
        if self._gs.is_overtime:
            self._period_combo.setCurrentIndex(self._period_combo.count() - 1)
        else:
            self._period_combo.setCurrentIndex(self._gs.period - 1)
        self._period_combo.blockSignals(False)

    def _on_period_changed(self, idx: int):
        if idx < 0:
            return
        ot_index = self._gs.sport_config.periods_count  # overtime is last item
        if self._gs.sport_config.has_overtime and idx == ot_index:
            self._gs.set_overtime(True)
        else:
            self._gs.set_overtime(False)
            self._gs.set_period(idx + 1)

    def _on_state_period(self, current: int, total: int):
        if self._gs.is_overtime:
            return  # overtime handles its own combo selection via _on_ot
        self._period_combo.blockSignals(True)
        self._period_combo.setCurrentIndex(current - 1)
        self._period_combo.blockSignals(False)

    def _sync_timer_mode(self):
        mode = self._gs.timer_mode
        self._btn_mode.blockSignals(True)
        self._btn_mode.setChecked(mode == "countup")
        self._btn_mode.setText("秒表" if mode == "countup" else "倒计时")
        self._btn_mode.blockSignals(False)
        self._sync_time_spinboxes()

    def _on_mode_toggle(self, checked: bool):
        mode = "countup" if checked else "countdown"
        self._gs.set_timer_mode(mode)

    def _on_timer_mode_state(self, mode: str):
        self._btn_mode.blockSignals(True)
        self._btn_mode.setChecked(mode == "countup")
        self._btn_mode.setText("秒表" if mode == "countup" else "倒计时")
        self._btn_mode.blockSignals(False)
        self._sync_time_spinboxes()

    def _sync_time_spinboxes(self):
        secs = self._gs.timer_seconds
        m, s = divmod(abs(secs), 60)
        self._time_min.blockSignals(True)
        self._time_sec.blockSignals(True)
        self._time_min.setValue(m)
        self._time_sec.setValue(s)
        self._time_min.blockSignals(False)
        self._time_sec.blockSignals(False)

    def _on_set_time(self):
        total = self._time_min.value() * 60 + self._time_sec.value()
        self._gs.set_timer_seconds(total)

    def _update_timer_display(self, seconds: int):
        m, s = divmod(abs(seconds), 60)
        prefix = "-" if seconds < 0 else ""
        self._time_label.setText(f"{prefix}{m:02d}:{s:02d}")
        self._sync_time_spinboxes()

    def _on_running(self, running: bool):
        self._btn_start.setEnabled(not running)
        self._btn_pause.setEnabled(running)

    def _on_timer_expired(self):
        self._status.showMessage("时间到！", 5000)

    def _on_ot(self, is_ot: bool):
        # Sync period combo to show overtime or restore current period
        self._period_combo.blockSignals(True)
        if is_ot:
            self._period_combo.setCurrentIndex(self._period_combo.count() - 1)
        else:
            self._period_combo.setCurrentIndex(self._gs.period - 1)
        self._period_combo.blockSignals(False)

    def _on_reset(self):
        gs = self._gs
        self._name_a.setText(gs.team_a_name)
        self._name_b.setText(gs.team_b_name)
        self._score_a.setText(str(gs.team_a_score))
        self._score_b.setText(str(gs.team_b_score))
        self._update_timer_display(gs.timer_seconds)
        self._btn_start.setEnabled(True)
        self._btn_pause.setEnabled(False)
        # Reset score colors to template originals
        self._score_a_color = self._score_a_original_color
        self._score_b_color = self._score_b_original_color
        self._score_a.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._score_a_color};")
        self._score_b.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._score_b_color};")

    def set_scoreboard_window(self, window):
        self._scoreboard_window = window
        self._scoreboard_window.visibility_changed.connect(self._on_scoreboard_visibility)
        self._scoreboard_window.template_loaded.connect(self._on_template_colors)

    def _on_template_colors(self, color_a: str, color_b: str):
        """Sync control panel score colors with the scoreboard template."""
        self._score_a_color = color_a
        self._score_b_color = color_b
        self._score_a_original_color = color_a
        self._score_b_original_color = color_b
        self._score_a.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color_a};")
        self._score_b.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color_b};")

    def _on_scoreboard_visibility(self, visible: bool):
        self._btn_show.setText("显示记分板" if not visible else "隐藏记分板")

    def _toggle_scoreboard(self):
        w = self._scoreboard_window
        if w.isVisible():
            w.hide()
            self._btn_show.setText("显示记分板")
        else:
            w.show()
            self._btn_show.setText("隐藏记分板")

    def _toggle_stay_on_top(self, checked: bool):
        self._btn_top.setText("取消悬浮置顶" if checked else "悬浮置顶")
        self._scoreboard_window.set_stay_on_top(checked)

    def _open_style_editor(self):
        tid = self._template_combo.currentData()
        if not tid:
            return
        template_dir = get_resource_path(os.path.join("templates", tid))
        if not os.path.isdir(template_dir):
            return
        editor = StyleEditor(template_dir, self._scoreboard_window, self)
        editor.exec()

    def _on_swap_colors(self):
        """Swap score label colors in the control panel."""
        self._score_a_color, self._score_b_color = self._score_b_color, self._score_a_color
        self._score_a.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._score_a_color};")
        self._score_b.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._score_b_color};")

    def _on_center_top(self):
        if self._scoreboard_window:
            self._scoreboard_window.center_at_screen_top()

    def closeEvent(self, event):
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
        super().closeEvent(event)
