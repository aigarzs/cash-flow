import pandas as pd

print("******** pandas settings ********")
pd.options.mode.copy_on_write = True
print(f"pd.options.mode.copy_on_write={pd.options.mode.copy_on_write}")
print("******** alchemy settings ********")
engine_echo = True
print(f"Engine echo={engine_echo}")
