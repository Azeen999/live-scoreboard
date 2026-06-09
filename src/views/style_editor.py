import json
import os
import shutil

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QScrollArea,
    QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QColorDialog, QMessageBox, QFileDialog, QFrame, QSlider,
    QInputDialog,
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor

from src.utils.resource_path import get_resource_path


class StyleEditor(QDialog):
    template_saved = Signal(str)  # 新模板目录名

    ELEMENT_LABELS = {
        "__background__": "背景",
        "__both_teams__": "两队设置",
        "__layout__": "位置",
        "team_a_name": "A队队名",
        "team_a_score": "A队比分",
        "team_b_name": "B队队名",
        "team_b_score": "B队比分",
        "timer": "计时器",
        "period": "节次",
        "vs_divider": "VS分隔",
    }

    # Elements to skip in the list (covered by 两队设置)
    _TEAM_IDS = {"team_a_name", "team_a_score", "team_b_name", "team_b_score"}

    def __init__(self, template_dir: str, scoreboard_window=None, parent=None):
        super().__init__(parent)
        self.template_dir = template_dir
        self.json_path = os.path.join(template_dir, "template.json")
        self._scoreboard_window = scoreboard_window
        self._data: dict = {}
        self._original_data: dict = {}
        self._load()
        self._build_ui()

    def _load(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        # Snapshot the original so "重置为默认" always works
        self._original_data = json.loads(json.dumps(self._data))

    def _save(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _build_ui(self):
        self.setWindowTitle("样式编辑器")
        self.resize(780, 600)

        root = QVBoxLayout(self)
        root.setSpacing(6)

        hint = QLabel("修改后点击「保存」生效  |  回车确认数值，Ctrl+S 保存")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(hint)

        body = QHBoxLayout()
        body.setSpacing(10)

        left = QVBoxLayout()
        left.addWidget(QLabel("元素"))
        self._list = QListWidget()
        self._list.setMinimumWidth(130)
        self._list.currentItemChanged.connect(self._on_select)
        left.addWidget(self._list)
        body.addLayout(left)

        right = QVBoxLayout()
        right.addWidget(QLabel("属性"))
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._props_form = None
        self._rebuild_props_container()
        right.addWidget(self._scroll)
        body.addLayout(right, 1)

        root.addLayout(body, 1)

        btns = QHBoxLayout()
        self._btn_reset = QPushButton("重置为默认")
        self._btn_reset.setAutoDefault(False)
        self._btn_reset.clicked.connect(self._on_reset)
        btns.addWidget(self._btn_reset)
        self._btn_close = QPushButton("关闭")
        self._btn_close.setAutoDefault(False)
        self._btn_close.clicked.connect(self.reject)
        btns.addWidget(self._btn_close)
        btns.addStretch()
        self._btn_save_preset = QPushButton("保存预设")
        self._btn_save_preset.setAutoDefault(False)
        self._btn_save_preset.setToolTip("将当前样式另存为一个新模板")
        self._btn_save_preset.clicked.connect(self._on_save_preset)
        btns.addWidget(self._btn_save_preset)
        self._btn_save = QPushButton("保存")
        self._btn_save.setAutoDefault(False)
        self._btn_save.setMinimumHeight(34)
        self._btn_save.setStyleSheet(
            "QPushButton { background-color: #00e676; color: #000; "
            "font-weight: bold; font-size: 14px; border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #00c853; }"
        )
        self._btn_save.clicked.connect(self._on_save)
        btns.addWidget(self._btn_save)
        root.addLayout(btns)

        self._populate_list()

    def _populate_list(self):
        self._list.clear()
        self._add_list_item("__background__", "背景")
        self._add_list_item("__both_teams__", "两队设置")
        for eid in self._data.get("elements", {}):
            if eid in self._TEAM_IDS:
                continue
            label = self.ELEMENT_LABELS.get(eid, eid)
            self._add_list_item(eid, label)
        self._add_list_item("__layout__", "位置")
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _add_list_item(self, eid: str, label: str):
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, eid)
        item.setSizeHint(item.sizeHint() + QSize(0, 6))
        self._list.addItem(item)

    def _rebuild_props_container(self):
        if self._props_form is not None:
            old_container = self._props_form.parentWidget()
            if old_container:
                old_container.setParent(None)
                old_container.deleteLater()
        container = QWidget()
        self._props_form = QFormLayout(container)
        self._props_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._props_form.setSpacing(6)
        self._props_form.setContentsMargins(8, 8, 8, 8)
        self._scroll.setWidget(container)

    def _on_select(self, current, previous):
        self._rebuild_props_container()

        if not current:
            return

        eid = current.data(Qt.ItemDataRole.UserRole)
        if eid == "__background__":
            self._build_background_props()
        elif eid == "__both_teams__":
            self._build_both_teams_props()
        elif eid == "__layout__":
            self._build_layout_props()
        else:
            self._build_element_props(eid)

    def _build_background_props(self):
        bg = self._data.setdefault("background", {})

        # Gradient toggle
        grad_cb = QCheckBox("使用渐变")
        grad_cb.setChecked(bg.get("gradient", False))
        grad_cb.setStyleSheet("color: #ccc; font-size: 12px;")
        grad_cb.toggled.connect(lambda checked: self._set(bg, "gradient", checked))
        self._props_form.addRow(grad_cb)

        self._add_color_picker("背景颜色", bg, "color", "#0d0d1a")
        self._add_opacity_slider("透明度", bg, "opacity")
        self._add_background_spin("圆角", bg, "border_radius", 0, 200)
        self._add_background_spin("边距", bg, "padding", 0, 200)

        # Always show gradient color pickers
        self._add_color_picker("渐变起始色", bg, "gradient_from", "#0d0d1a")
        self._add_color_picker("渐变结束色", bg, "gradient_to", "#1a1a3a")

        img = bg.get("image", "")
        if img:
            img_label = QLabel(img)
            img_label.setStyleSheet("color: #aaa; font-size: 11px;")
            self._props_form.addRow("背景图片", img_label)

    def _add_opacity_slider(self, label: str, container: dict, key: str):
        row = QHBoxLayout()
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        val = int(container.get(key, 1.0) * 100)
        slider.setValue(val)
        val_label = QLabel(f"{val}%")
        val_label.setFixedWidth(40)

        def on_change(v):
            opacity = v / 100.0
            container[key] = opacity
            val_label.setText(f"{v}%")
            if self._scoreboard_window:
                self._scoreboard_window.set_opacity(opacity)

        slider.valueChanged.connect(on_change)
        row.addWidget(slider)
        row.addWidget(val_label)
        self._props_form.addRow(label, row)

    def _add_background_spin(self, label: str, container: dict, key: str,
                              min_v: int, max_v: int):
        """Spin box with live preview on the scoreboard window."""
        w = QSpinBox()
        w.setRange(min_v, max_v)
        w.setValue(container.get(key, min_v))
        w.setSuffix(" px")
        w.valueChanged.connect(lambda v: self._set(container, key, v))
        # Live preview
        method_map = {
            "border_radius": "set_border_radius",
            "padding": "set_padding",
        }
        if self._scoreboard_window and key in method_map:
            w.valueChanged.connect(
                lambda v: getattr(self._scoreboard_window, method_map[key])(v)
            )
        self._props_form.addRow(label, w)

    # ── single-element props (color + font + visibility, no position) ──

    def _build_element_props(self, eid: str):
        elems = self._data.setdefault("elements", {})
        elem = elems.setdefault(eid, {"type": "label", "geometry": {}})

        self._add_color_picker("文字颜色", elem, "color", "#ffffff")
        self._add_spin_int("字体大小", elem, "font_size", 8, 500)

    # ── both-teams props (name + score per team, no position) ──

    def _build_both_teams_props(self):
        elems = self._data.setdefault("elements", {})
        team_pairs = [
            ("A队", "team_a_name", "team_a_score"),
            ("B队", "team_b_name", "team_b_score"),
        ]

        for team_label, name_id, score_id in team_pairs:
            sep = QLabel(f"── {team_label} ──")
            sep.setStyleSheet("color: #aaa; font-weight: bold; margin-top: 8px;")
            self._props_form.addRow(sep)

            name_elem = elems.setdefault(name_id, {"type": "label", "geometry": {}})
            score_elem = elems.setdefault(score_id, {"type": "digits", "geometry": {}, "min_digits": 2})

            name_lbl = QLabel("  队名")
            name_lbl.setStyleSheet("color: #ccc; font-size: 11px;")
            self._props_form.addRow(name_lbl)
            self._add_color_picker("    颜色", name_elem, "color", "#ffffff")
            self._add_spin_int("    字体大小", name_elem, "font_size", 8, 500)

            score_lbl = QLabel("  比分")
            score_lbl.setStyleSheet("color: #ccc; font-size: 11px;")
            self._props_form.addRow(score_lbl)
            self._add_color_picker("    颜色", score_elem, "color", "#ffffff")
            self._add_spin_int("    字体大小", score_elem, "font_size", 8, 500)

    # ── unified layout editor ──

    def _build_layout_props(self):
        """Unified layout editor: X/Y only, live preview on change."""
        elems = self._data.setdefault("elements", {})

        hint = QLabel("拖动或输入 X/Y 数值（0~1），计分板实时预览")
        hint.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 4px;")
        self._props_form.addRow(hint)

        # Column headers
        header = QHBoxLayout()
        header.setSpacing(6)
        for text, w in [("元素", 80), ("X", 120), ("Y", 120), ("显示", 50)]:
            lbl = QLabel(text)
            lbl.setFixedWidth(w)
            lbl.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
            header.addWidget(lbl)
        header.addStretch()
        self._props_form.addRow(header)

        for eid in elems:
            if eid == "placeholder_none":
                continue

            elem = elems[eid]
            geo = elem.setdefault("geometry", {})

            row = QHBoxLayout()
            row.setSpacing(6)

            name_label = QLabel(self.ELEMENT_LABELS.get(eid, eid))
            name_label.setFixedWidth(80)
            name_label.setStyleSheet("color: #ccc; font-size: 12px;")
            row.addWidget(name_label)

            for key in ("x", "y"):
                sb = QDoubleSpinBox()
                sb.setRange(0.0, 1.0)
                sb.setDecimals(2)
                sb.setSingleStep(0.01)
                sb.setFixedWidth(120)
                sb.setValue(geo.get(key, 0.0))
                sb.setStyleSheet("font-size: 13px;")
                sb.valueChanged.connect(
                    lambda v, eid=eid, g=geo, k=key:
                    self._on_position_changed(eid, g, k, round(v, 2))
                )
                row.addWidget(sb)

            # Visibility checkbox
            vis_cb = QCheckBox()
            vis_cb.setChecked(elem.get("visible", True))
            vis_cb.setFixedWidth(50)
            vis_cb.setToolTip("显示/隐藏")
            vis_cb.toggled.connect(
                lambda checked, el=elem: self._set(el, "visible", checked)
            )
            row.addWidget(vis_cb)

            row.addStretch()
            self._props_form.addRow(row)

    def _on_position_changed(self, eid: str, geo: dict, key: str, value: float):
        """Update data AND push live update to scoreboard."""
        self._set(geo, key, value)
        if self._scoreboard_window:
            self._scoreboard_window.update_element_position(eid, {key: value})

    # ── visibility helper ──

    def _add_visibility_checkbox(self, elem: dict):
        cb = QCheckBox("显示在记分板上")
        cb.setChecked(elem.get("visible", True))
        cb.setStyleSheet("color: #ccc; font-size: 11px;")
        cb.toggled.connect(lambda checked, e=elem: self._set(e, "visible", checked))
        self._props_form.addRow(cb)

    # ── generic widget builders ──

    def _add_spin_int(self, label: str, container: dict, key: str,
                      min_v: int, max_v: int):
        w = QSpinBox()
        w.setRange(min_v, max_v)
        w.setValue(container.get(key, min_v))
        w.valueChanged.connect(lambda v: self._set(container, key, v))
        self._props_form.addRow(label, w)

    def _add_spin_float(self, label: str, container: dict, key: str,
                        min_v: float, max_v: float, decimals: int,
                        step: float):
        w = QDoubleSpinBox()
        w.setRange(min_v, max_v)
        w.setDecimals(decimals)
        w.setSingleStep(step)
        w.setValue(container.get(key, min_v))
        w.valueChanged.connect(lambda v: self._set(container, key,
                                                    round(v, decimals)))
        self._props_form.addRow(label, w)

    def _add_color_picker(self, label: str, container: dict, key: str,
                          default: str = "#ffffff"):
        row = QHBoxLayout()
        color_btn = QPushButton()
        color_btn.setFixedSize(48, 28)
        hex_input = QLineEdit(container.get(key, default))
        hex_input.setFixedWidth(100)

        def update_preview(hex_color: str):
            h = hex_color.strip()
            if not h.startswith("#"):
                h = "#" + h
            color_btn.setStyleSheet(
                f"background-color: {h}; border: 1px solid #555; border-radius: 3px;"
            )

        def on_pick():
            current = hex_input.text().strip()
            qcolor = QColor(current) if QColor.isValidColor(current) else QColor(default)
            chosen = QColorDialog.getColor(qcolor, self, f"选择颜色 - {label}")
            if chosen.isValid():
                hex_val = chosen.name()
                hex_input.setText(hex_val)
                self._set(container, key, hex_val)

        def on_text(text: str):
            t = text.strip()
            normalized = t if t.startswith("#") else f"#{t}"
            if QColor.isValidColor(normalized):
                self._set(container, key, normalized)
                update_preview(normalized)

        color_btn.clicked.connect(on_pick)
        hex_input.textChanged.connect(on_text)
        update_preview(container.get(key, default))

        row.addWidget(color_btn)
        row.addWidget(hex_input)
        row.addStretch()
        self._props_form.addRow(label, row)

    @staticmethod
    def _set(container: dict, key: str, value):
        container[key] = value

    # ── save / export / reset ──

    def _sync_background(self):
        """Push all background properties to the scoreboard window."""
        if not self._scoreboard_window:
            return
        bg = self._data.get("background", {})
        self._scoreboard_window.set_opacity(bg.get("opacity", 1.0))
        self._scoreboard_window.set_border_radius(bg.get("border_radius", 0))
        self._scoreboard_window.set_padding(bg.get("padding", 0))

    def _on_save(self):
        try:
            self._save()
            self._sync_background()
            QMessageBox.information(self, "已保存",
                                    "template.json 已保存，计分板自动更新。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _on_save_preset(self):
        """Save current style as a new named template under templates/."""
        name, ok = QInputDialog.getText(
            self, "保存预设", "预设名称:",
            text="",
        )
        if not ok or not name or not name.strip():
            return
        name = name.strip()

        # Sanitize filename
        safe_name = "".join(
            c for c in name
            if c.isalnum() or c in "._- ()（）"
        ).strip()
        if not safe_name:
            safe_name = "未命名"

        target_dir = get_resource_path(os.path.join("templates", safe_name))
        target_json = os.path.join(target_dir, "template.json")

        # Check if already exists
        if os.path.exists(target_dir):
            reply = QMessageBox.question(
                self, "覆盖确认",
                f"模板「{safe_name}」已存在，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            os.makedirs(target_dir, exist_ok=True)

            # Save template.json
            with open(target_json, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)

            # Copy background image if present
            bg = self._data.get("background", {})
            bg_image = bg.get("image", "")
            if bg_image:
                src_img = os.path.join(self.template_dir, bg_image)
                if os.path.isfile(src_img):
                    shutil.copy2(src_img, os.path.join(target_dir, bg_image))

            self.template_saved.emit(safe_name)
            QMessageBox.information(self, "已保存",
                                    f"预设「{safe_name}」已保存，可在控制面板模板中选择。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _on_reset(self):
        reply = QMessageBox.question(
            self, "确认重置",
            "重置为默认值？当前所有修改将丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Restore from the snapshot taken when editor opened
            self._data = json.loads(json.dumps(self._original_data))
            # Write back to file so scoreboard also reverts
            self._save()
            if self._scoreboard_window:
                self._scoreboard_window.load_template(self.template_dir)
            current = self._list.currentItem()
            if current:
                self._on_select(current, None)
