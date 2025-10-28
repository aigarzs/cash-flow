import sys, os

def resource_path(rel_path: str) -> str:
    # Works for development and PyInstaller tmp directory
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)