"""Read-only assets from source checkout or a bundled desktop executable."""
import sys
from pathlib import Path


def app_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'app'
    return Path(__file__).resolve().parent


def templates_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'templates'
    return Path(__file__).resolve().parents[1] / 'templates'


def vendor_dir():
    return app_dir() / 'vendor_py'
