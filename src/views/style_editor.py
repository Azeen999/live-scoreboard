import json
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QScrollArea,
    QSpinBox, QDoubleSpinBox, QLineEdit,
    QColorDialog, QMessageBox, QFileDialog, QFrame, QSlider,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor


class StyleEditor(QDialog):
    ELEMENT_LABELS = {
        "__background__": "背景",
        "timer": "计时器", "period": "节次", "overtime": "加时赛",
        "team_a_name": "A队名", "team_a_score": "A队比分",
        "team_b_name": "B队名", "team_b_score": "B队比分",
        "vs_divider": "VS",
    }

    def __init__(self, template_dir: str, scoreboard_window=None, parent=None):
        super().__init__(parent)
        self.template_dir = template_dir
        self.json_path = os.path.join(template_dir, "template.json")
        self._scoreboard_window = scoreboard_window
        self._data: dict = {}
        self._load()
        self._build_ui()

    def _load(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def _save(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _build_ui(self):
        self.setWindowTitle("样式编辑器")
        self.resize(680, 520)

        root = QVBoxLayout(self)
        root.setSpacing(6)

        hint = QLabel("修改后点击「保存」生效")
        hint.setStyleSheet("color: #888; font-size: 12px;")
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._props_container = QWidget()
        self._props_form = QFormLayout(self._props_container)
        self._props_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._props_form.setSpacing(6)
        self._props_form.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(self._props_container)
        right.addWidget(scroll)
        body.addLayout(right, 1)

        root.addLayout(body, 1)

        btns = QHBoxLayout()
        self._btn_reset = QPushButton("重置为默认")
        self._btn_reset.clicked.connect(self._on_reset)
        btns.addWidget(self._btn_reset)
        btns.addStretch()
        self._btn_export = QPushButton("另存为...")
        self._btn_export.clicked.connect(self._on_export)
        btns.addWidget(self._btn_export)
        self._btn_save = QPushButton("保存")
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
        for eid in self._data.get("elements", {}):
            label = self.ELEMENT_LABELS.get(eid, eid)
            self._add_list_item(eid, label)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _add_list_item(self, eid: str, label: str):
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, eid)
        item.setSizeHint(item.sizeHint() + QSize(0, 6))
        self._list.addItem(item)

    def _on_select(self, current, previous):
        while self._props_form.count():
            item = self._props_form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not current:
            return

        eid = current.data(Qt.ItemDataRole.UserRole)
        if eid == "__background__":
            self._build_background_props()
        else:
            self._build_element_props(eid)

    def _build_background_props(self):
        bg = self._data.setdefault("background", {})
        self._add_color_picker("背景颜色", bg, "color", "#0d0d1a")

        self._add_opacity_slider("透明度", bg, "opacity")

        has_gradient = bg.get("gradient", False)
        if has_gradient:
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
            container[key] = v / 100.0
            val_label.setText(f"{v}%")

        slider.valueChanged.connect(on_change)
        row.addWidget(slider)
        row.addWidget(val_label)
        self._props_form.addRow(label, row)

    def _build_element_props(self, eid: str):
        elems = self._data.setdefault("elements", {})
        elem = elems.setdefault(eid, {"type": "label", "geometry": {}})
        geo = elem.setdefault("geometry", {})

        self._add_color_picker("文字颜色", elem, "color", "#ffffff")
        self._add_spin_int("字体大小", elem, "font_size", 8, 500)

        self._props_form.addRow(" ", QLabel(""))

        self._add_spin_float("位置 X", geo, "x", 0, 1, 2, 0.01)
        self._add_spin_float("位置 Y", geo, "y", 0, 1, 2, 0.01)
        self._add_spin_float("宽度", geo, "w", 0, 1, 2, 0.01)
        self._add_spin_float("高度", geo, "h", 0, 1, 2, 0.01)

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

    def _on_save(self):
        try:
            self._save()
            if self._scoreboard_window:
                opacity = self._data.get("background", {}).get("opacity", 1.0)
                self._scoreboard_window.set_opacity(opacity)
            QMessageBox.information(self, "已保存",
                                    "template.json 已保存，计分板自动更新。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为模板", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "已导出", f"已保存到:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))

    def _on_reset(self):
        reply = QMessageBox.question(
            self, "确认重置",
            "重置为默认值？当前所有修改将丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._load()
            current = self._list.currentItem()
            if current:
                self._on_select(current, None)
