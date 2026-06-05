from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel,
                               QVBoxLayout)
from PySide6.QtCore import Qt, QTimer, QFileSystemWatcher, Signal
import os
from PySide6.QtGui import (QPainter, QLinearGradient, QColor, QFont, QPixmap,
                           QMouseEvent, QPainterPath)

from src.models.game_state import GameState
from src.templates.template_config import TemplateConfig, load_template, ElementConfig
from PySide6.QtWidgets import QMenu


class ScoreboardCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._template_config: TemplateConfig | None = None
        self._cached_pixmap: QPixmap | None = None
        self._cached_image_path: str = ""
        self._scale_factor: float = 1.0
        self._widgets: dict[str, QWidget] = {}
        self.setAutoFillBackground(False)

    def set_config(self, config: TemplateConfig | None):
        self._template_config = config
        self._load_image()
        self._rebuild_elements()
        self.update()

    def _load_image(self):
        self._cached_pixmap = None
        self._cached_image_path = ""
        if not self._template_config:
            return
        bg = self._template_config.background
        if bg.image:
            img_path = os.path.join(self._template_config.template_dir, bg.image)
            if os.path.isfile(img_path):
                self._cached_pixmap = QPixmap(img_path)
                self._cached_image_path = img_path

    def _rebuild_elements(self):
        for w in self._widgets.values():
            w.setParent(None)
            w.deleteLater()
        self._widgets.clear()
        if not self._template_config:
            return
        for elem_id, elem in self._template_config.elements.items():
            w = self._create_element(elem_id, elem)
            self._widgets[elem_id] = w
        # Ensure timer (and period) render on top of score widgets
        for top_id in ("timer", "period"):
            top_w = self._widgets.get(top_id)
            if top_w:
                top_w.raise_()
        self._reposition_overlays()

    def _create_element(self, elem_id: str, elem: ElementConfig) -> QWidget:
        label = QLabel(self)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        is_digits = elem.type in ("digits", "timer")
        font_family = elem.font_family or self._template_config.font_family
        if is_digits:
            font_family = "Consolas"
        font = QFont(font_family)
        font.setBold(True)
        font.setPixelSize(max(10, int(elem.font_size * self._scale_factor)))
        label.setFont(font)
        align_map = {
            "left": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "right": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "center": Qt.AlignmentFlag.AlignCenter,
        }
        label.setAlignment(align_map.get(elem.alignment, Qt.AlignmentFlag.AlignCenter))
        ss = f"color: {elem.color}; background: transparent; padding: 0px; margin: 0px;"
        if is_digits:
            ss += " letter-spacing: 2px;"
        label.setStyleSheet(ss)
        if elem.type == "digits":
            label.setText("0" * elem.min_digits)
        elif elem.type == "timer":
            label.setText("00:00")
        elif elem_id == "vs_divider":
            label.setText("VS")
        label.setVisible(elem.visible)
        return label

    def get_widget(self, elem_id: str) -> QWidget | None:
        return self._widgets.get(elem_id)

    def reposition(self):
        self._reposition_overlays()

    def _reposition_overlays(self):
        if not self._template_config:
            return
        cw = self.width()
        ch = self.height()
        if cw <= 0 or ch <= 0:
            return
        sf = self._scale_factor
        for elem_id, elem in self._template_config.elements.items():
            widget = self._widgets.get(elem_id)
            if not widget:
                continue
            geo = elem.geometry
            x = int(geo["x"] * cw)
            y = int(geo["y"] * ch)
            ew = int(geo["w"] * cw)
            eh = int(geo["h"] * ch)
            if isinstance(widget, QLabel):
                desired_px = max(10, int(elem.font_size * sf))
                font = widget.font()
                font.setPixelSize(max(8, desired_px))
                widget.setFont(font)
                # Auto-expand widget to fit actual text size
                fm = widget.fontMetrics()
                text_w = fm.horizontalAdvance(widget.text()) + 4
                text_h = fm.height() + 4
                if text_w > ew:
                    x = x - (text_w - ew) // 2
                    ew = text_w
                if text_h > eh:
                    y = y - (text_h - eh) // 2
                    eh = text_h
                # Clamp to canvas bounds
                if x < 0:
                    x = 0
                if y < 0:
                    y = 0
                if x + ew > cw:
                    ew = cw - x
                if y + eh > ch:
                    eh = ch - y
            widget.setGeometry(x, y, ew, eh)

    def set_scale_factor(self, sf: float):
        self._scale_factor = sf

    def _bg_rect(self):
        """Returns the background rect adjusted for padding."""
        r = self.rect()
        p = self._template_config.background.padding if self._template_config else 0
        return r.adjusted(p, p, -p, -p)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._template_config:
            bg = self._template_config.background
            br = self._bg_rect()
            radius = bg.border_radius
            if radius > 0:
                clip = QPainterPath()
                clip.addRoundedRect(br, radius, radius)
            else:
                clip = QPainterPath()
                clip.addRect(br)

            if self._cached_pixmap and not self._cached_pixmap.isNull():
                painter.setOpacity(bg.opacity)
                painter.setClipPath(clip)
                scaled = self._cached_pixmap.scaled(
                    br.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                x = br.x() + (br.width() - scaled.width()) // 2
                y = br.y() + (br.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
                painter.setClipping(False)
                painter.setOpacity(1.0)
            elif bg.gradient:
                c1, c2 = QColor(bg.gradient_from), QColor(bg.gradient_to)
                c1.setAlphaF(bg.opacity)
                c2.setAlphaF(bg.opacity)
                gradient = QLinearGradient(br.topLeft(), br.bottomLeft())
                gradient.setColorAt(0.0, c1)
                gradient.setColorAt(1.0, c2)
                painter.fillPath(clip, gradient)
            else:
                c = QColor(bg.color)
                c.setAlphaF(bg.opacity)
                painter.fillPath(clip, c)
        else:
            painter.fillRect(self.rect(), QColor("#0a0a1a"))
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_overlays()


class ScoreboardWindow(QMainWindow):
    visibility_changed = Signal(bool)
    template_loaded = Signal(str, str)  # (score_a_color, score_b_color)

    def __init__(self, game_state: GameState):
        super().__init__()
        self._gs = game_state
        self._template_config: TemplateConfig | None = None
        self._scale_factor: float = 1.0
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blinking = False
        self._blink_visible = True
        self._blink_label = None
        self._drag_pos = None
        self._stay_on_top = False
        self._resize_mode = False
        self._resize_edge = None  # 'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'
        self._resize_margin = 8
        self._original_opacity: float = 1.0

        self._template_dir = ""
        self._file_watcher = QFileSystemWatcher(self)
        self._file_watcher.fileChanged.connect(self._on_template_file_changed)
        self._reload_debounce = QTimer(self)
        self._reload_debounce.setSingleShot(True)
        self._reload_debounce.timeout.connect(self._do_reload_template)

        self.setWindowTitle("粗趣计分 - 记分板")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(820, 170)
        self.setMinimumSize(400, 80)

        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._canvas = ScoreboardCanvas()
        layout.addWidget(self._canvas)

        self._sides_swapped = False
        self._score_a_color = "#ffffff"
        self._score_b_color = "#ffffff"

        self._connect_signals()

    def _connect_signals(self):
        gs = self._gs
        gs.team_a_name_changed.connect(lambda v: self._update_label("team_a_name", v))
        gs.team_b_name_changed.connect(lambda v: self._update_label("team_b_name", v))
        gs.team_a_score_changed.connect(lambda v: self._update_digits("team_a_score", v))
        gs.team_b_score_changed.connect(lambda v: self._update_digits("team_b_score", v))
        gs.period_changed.connect(self._update_period)
        gs.timer_seconds_changed.connect(self._update_timer)
        gs.overtime_changed.connect(self._update_overtime)
        gs.scores_reset.connect(self._on_reset)
        gs.sides_swapped.connect(self._on_sides_swapped)
        gs.sport_changed.connect(lambda _: self._on_reset())

    def load_template(self, template_dir: str):
        for p in self._file_watcher.files():
            self._file_watcher.removePath(p)

        config = load_template(template_dir)
        self._template_config = config
        self._template_dir = template_dir
        self._original_opacity = config.background.opacity

        rw = config.resolution_width
        rh = config.resolution_height
        self._scale_factor = min(self.width() / rw, self.height() / rh)
        self._canvas.set_scale_factor(self._scale_factor)
        self._canvas.set_config(config)

        # Store original score colors for side-swap
        a_cfg = config.elements.get("team_a_score")
        b_cfg = config.elements.get("team_b_score")
        self._score_a_color = a_cfg.color if a_cfg else "#ffffff"
        self._score_b_color = b_cfg.color if b_cfg else "#ffffff"
        self._sides_swapped = False

        json_path = os.path.join(template_dir, "template.json")
        if os.path.exists(json_path):
            self._file_watcher.addPath(json_path)

        self._on_reset()

        self.resize(max(400, rw // 3), max(80, rh // 3))
        self.template_loaded.emit(self._score_a_color, self._score_b_color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rw = self._template_config.resolution_width if self._template_config else 1920
        rh = self._template_config.resolution_height if self._template_config else 1080
        self._scale_factor = min(self.width() / rw, self.height() / rh)
        self._canvas.set_scale_factor(self._scale_factor)
        self._canvas.reposition()

    def _on_template_file_changed(self, path: str):
        if path not in self._file_watcher.files() and os.path.exists(path):
            self._file_watcher.addPath(path)
        if self._reload_debounce.isActive():
            self._reload_debounce.stop()
        self._reload_debounce.start(300)

    def _do_reload_template(self):
        if not self._template_dir:
            return
        json_path = os.path.join(self._template_dir, "template.json")
        if not os.path.exists(json_path):
            return
        try:
            self.load_template(self._template_dir)
        except Exception as e:
            print(f"[Scoreboard] 模板热重载失败: {e}")

    def _update_label(self, elem_id: str, text: str):
        w = self._canvas.get_widget(elem_id)
        if isinstance(w, QLabel):
            w.setText(text)

    def _update_digits(self, elem_id: str, value: int):
        w = self._canvas.get_widget(elem_id)
        if isinstance(w, QLabel):
            cfg = self._template_config
            elem = cfg.elements.get(elem_id) if cfg else None
            digits = elem.min_digits if elem else 2
            w.setText(str(value).zfill(digits))

    def _update_period(self, current: int, total: int):
        gs = self._gs
        if gs.is_overtime:
            label = gs.sport_config.overtime_label
        else:
            labels = gs.sport_config.period_labels
            label = labels[current - 1] if current - 1 < len(labels) else str(current)
        self._update_label("period", label)

    def _update_timer(self, seconds: int):
        w = self._canvas.get_widget("timer")
        if not isinstance(w, QLabel):
            return
        cfg = self._template_config
        elem = cfg.elements.get("timer") if cfg else None
        fmt = elem.format if elem else "mm:ss"

        neg = seconds < 0
        secs = abs(seconds)
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        prefix = "-" if neg else ""

        if "h" in fmt.lower():
            text = f"{prefix}{h:02d}:{m:02d}:{s:02d}"
        else:
            text = f"{prefix}{m:02d}:{s:02d}"
        w.setText(text)

        should_blink = (seconds <= 10 and seconds > 0
                        and self._gs.timer_mode == "countdown"
                        and self._gs.is_running)
        if should_blink and not self._blinking:
            self._start_blink(w, elem)

    def _start_blink(self, label: QLabel, elem: ElementConfig | None):
        self._blinking = True
        self._blink_label = label
        self._blink_normal_color = elem.color if elem else "#ffffff"
        self._blink_timer.start(500)

    def _toggle_blink(self):
        if not self._blinking or not self._blink_label:
            return
        self._blink_visible = not self._blink_visible
        color = self._blink_normal_color if self._blink_visible else "#ff4444"
        self._blink_label.setStyleSheet(
            f"color: {color}; background: transparent; padding: 0px;"
        )
        if self._gs.timer_seconds > 10 or not self._gs.is_running:
            self._stop_blink()

    def _stop_blink(self):
        self._blinking = False
        self._blink_timer.stop()
        if self._blink_label:
            self._blink_label.setStyleSheet(
                f"color: {self._blink_normal_color}; background: transparent; padding: 0px;"
            )

    def _update_overtime(self, is_ot: bool):
        # Overtime is shown via the period label (switches to overtime_label)
        gs = self._gs
        self._update_period(gs.period, gs.periods_count)

    def _on_reset(self):
        gs = self._gs
        self._update_label("team_a_name", gs.team_a_name)
        self._update_label("team_b_name", gs.team_b_name)
        self._update_digits("team_a_score", gs.team_a_score)
        self._update_digits("team_b_score", gs.team_b_score)
        self._update_timer(gs.timer_seconds)
        self._update_period(gs.period, gs.periods_count)
        self._update_overtime(gs.is_overtime)
        self._stop_blink()
        self._sides_swapped = False
        self._apply_score_colors()

    def _on_sides_swapped(self):
        self._sides_swapped = not self._sides_swapped
        self._apply_score_colors()

    def _apply_score_colors(self):
        """Apply score colors, swapping if sides are swapped."""
        color_a = self._score_b_color if self._sides_swapped else self._score_a_color
        color_b = self._score_a_color if self._sides_swapped else self._score_b_color
        for eid, color in [("team_a_score", color_a), ("team_b_score", color_b)]:
            w = self._canvas.get_widget(eid)
            if isinstance(w, QLabel):
                w.setStyleSheet(
                    f"color: {color}; background: transparent; padding: 0px; margin: 0px; letter-spacing: 2px;"
                )

    def set_stay_on_top(self, enabled: bool):
        self._stay_on_top = enabled
        was_visible = self.isVisible()
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

    def center_at_screen_top(self):
        """Center the scoreboard window at the top of the screen."""
        from PySide6.QtGui import QScreen
        screen = self.screen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y()
        self.move(x, y)
        if not self.isVisible():
            self.show()

    def update_element_position(self, eid: str, geo: dict):
        """Live-update a single element's geometry without full reload."""
        if self._template_config and eid in self._template_config.elements:
            elem = self._template_config.elements[eid]
            for k in ("x", "y", "w", "h"):
                if k in geo:
                    elem.geometry[k] = geo[k]
            self._canvas.reposition()

    def set_opacity(self, opacity: float):
        """Update background opacity without rebuilding overlay widgets."""
        if self._template_config:
            self._template_config.background.opacity = opacity
        self._canvas.update()

    def set_border_radius(self, radius: int):
        """Update background border radius without rebuilding."""
        if self._template_config:
            self._template_config.background.border_radius = radius
        self._canvas.update()

    def set_padding(self, padding: int):
        """Update background padding without rebuilding."""
        if self._template_config:
            self._template_config.background.padding = padding
        self._canvas.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Q:
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()
        else:
            super().keyPressEvent(event)

    def _get_edge(self, pos):
        """Detect which edge the mouse is near. Returns None if not near an edge."""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = self._resize_margin
        edge = ""
        if y < m:
            edge += "n"
        elif y > h - m:
            edge += "s"
        if x < m:
            edge += "w"
        elif x > w - m:
            edge += "e"
        return edge or None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._resize_mode:
                edge = self._get_edge(event.pos())
                if edge:
                    self._resize_edge = edge
                    self._drag_pos = event.globalPosition().toPoint()
                    return
            self._resize_edge = None
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resize_edge and event.buttons() & Qt.MouseButton.LeftButton:
            # Resizing
            delta = event.globalPosition().toPoint() - self._drag_pos
            g = self.geometry()
            if "e" in self._resize_edge:
                g.setWidth(max(self.minimumWidth(), g.width() + delta.x()))
            if "s" in self._resize_edge:
                g.setHeight(max(self.minimumHeight(), g.height() + delta.y()))
            if "w" in self._resize_edge:
                new_w = max(self.minimumWidth(), g.width() - delta.x())
                g.setX(g.x() + g.width() - new_w)
                g.setWidth(new_w)
            if "n" in self._resize_edge:
                new_h = max(self.minimumHeight(), g.height() - delta.y())
                g.setY(g.y() + g.height() - new_h)
                g.setHeight(new_h)
            self.setGeometry(g)
            self._drag_pos = event.globalPosition().toPoint()
        elif event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        elif self._resize_mode and not event.buttons():
            # Update cursor
            edge = self._get_edge(event.pos())
            cursors = {
                "n": Qt.CursorShape.SizeVerCursor,
                "s": Qt.CursorShape.SizeVerCursor,
                "e": Qt.CursorShape.SizeHorCursor,
                "w": Qt.CursorShape.SizeHorCursor,
                "ne": Qt.CursorShape.SizeBDiagCursor,
                "sw": Qt.CursorShape.SizeBDiagCursor,
                "nw": Qt.CursorShape.SizeFDiagCursor,
                "se": Qt.CursorShape.SizeFDiagCursor,
            }
            self.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        self._resize_edge = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        top_act = menu.addAction("取消置顶" if self._stay_on_top else "置顶")
        resize_act = menu.addAction("锁定大小" if self._resize_mode else "改变大小")
        hide_act = menu.addAction("隐藏")
        quit_act = menu.addAction("关闭所有")
        act = menu.exec(event.globalPos())
        if act == top_act:
            self.set_stay_on_top(not self._stay_on_top)
        elif act == resize_act:
            self._resize_mode = not self._resize_mode
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif act == hide_act:
            self.hide()
        elif act == quit_act:
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def showEvent(self, event):
        super().showEvent(event)
        self.visibility_changed.emit(True)
        QTimer.singleShot(0, self._canvas.reposition)
