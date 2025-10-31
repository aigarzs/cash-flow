import logging

import pandas as pd

logLevel = logging.DEBUG
pd.options.mode.copy_on_write = True
pd.set_option('future.no_silent_downcasting', True)
engine_echo = False
