import os
import sys


def get_resource_path(relative_path: str) -> str:
    """Returns the path to a resource, preferring external (next to exe) over bundled."""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        external = os.path.join(exe_dir, relative_path)
        if os.path.exists(external):
            return external
        return os.path.join(sys._MEIPASS, relative_path)  # type: ignore[attr-defined]
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_path, relative_path)


def list_resource_dirs(relative_path: str) -> list[str]:
    """Lists subdirectories in a resource path, merging external + bundled locations."""
    dirs: set[str] = set()
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        external = os.path.join(exe_dir, relative_path)
        if os.path.isdir(external):
            for name in os.listdir(external):
                if os.path.isdir(os.path.join(external, name)):
                    dirs.add(name)
        bundled = os.path.join(sys._MEIPASS, relative_path)  # type: ignore[attr-defined]
        if os.path.isdir(bundled):
            for name in os.listdir(bundled):
                if os.path.isdir(os.path.join(bundled, name)):
                    dirs.add(name)
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        path = os.path.join(base_path, relative_path)
        if os.path.isdir(path):
            for name in os.listdir(path):
                if os.path.isdir(os.path.join(path, name)):
                    dirs.add(name)
    return sorted(dirs)
