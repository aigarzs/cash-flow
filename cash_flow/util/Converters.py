from datetime import datetime, date
from decimal import Decimal
import numpy as np
import pandas as pd

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush


def decimal_format():
    return "{:.2f}"

def date_format():
    return "%d. %b, %Y"

def str_to_date(date_string):
    patterns = ["%d", "%d.%m", "%d-%m", "%y.%m.%d", "%y-%m-%d", "%Y.%m.%d", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]

    for format in patterns:
        try:
            d = datetime.strptime(date_string, format)
            if "%y" not in format and "%Y" not in format:
                d = d.replace(year=datetime.now().year)
            if "%m" not in format:
                d = d.replace(month=datetime.now().month)
            return d
        except:
            continue


    return datetime.now()

def str_to_priority(priority_string):
    try:
        return int(priority_string)
    except:
        return 100


def pandas_to_python(value):
    """Convert a Pandas or NumPy value to a native Python type."""
    if isinstance(value, np.generic):  # Convert NumPy scalar types
        return value.item()
    elif isinstance(value, pd.Timestamp):  # Convert Pandas Timestamp to Python datetime
        return value.to_pydatetime() if not pd.isna(value) else None
    elif isinstance(value, pd.Timedelta):  # Convert Pandas Timedelta to Python timedelta
        return value.to_pytimedelta()
    elif pd.isna(value):  # Handles NaN, None, pd.NA, pd.NaT
        return None
    return value  # Return as-is for other Python-native types

def various_to_integer(value):
    try:
        return int(float(value))
    except:
        return 0


if __name__ == "__main__":
    print(str_to_date("2021-01-05 00:00:00"))
    print(str_to_date("25.03"))
    print(various_to_integer("a"))
    print(various_to_integer("3.3"))