import logging

import pandas as pd

print("******** logging settings *******")
logLevel = logging.DEBUG
print(f"Log level={logLevel}")
print("******** pandas settings ********")
pd.options.mode.copy_on_write = True
print(f"pd.options.mode.copy_on_write={pd.options.mode.copy_on_write}")
print("******** alchemy settings ********")
engine_echo = False
print(f"Engine echo={engine_echo}")
print()
print("************ EOF settings *****************")
print()
