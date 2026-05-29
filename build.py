"""Build script: packages the scoreboard app into a single .exe using PyInstaller."""

import os
import sys


def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sep = os.pathsep

    args = [
        os.path.join(base_dir, "main.py"),
        "--name=粗趣计分",
        "--onefile",
        "--windowed",
        "--add-data=" + os.path.join(base_dir, "templates") + sep + "templates",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--clean",
        "--noconfirm",
    ]

    import PyInstaller.__main__
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    build()
