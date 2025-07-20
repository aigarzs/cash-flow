from sqlalchemy import create_engine
from cash_flow.util.Settings import engine_echo

engine_db = create_engine("sqlite:///../../data/database.db", echo=engine_echo)

username = "genie@inbox.lv"
password = "fisJMLfHsto7q-C!^7(J[5G7VHfTj7"
server = "jumiscloud.mansjumis.lv,12878"  # Use double backslashes for instance names
database = "alfreds"

connection_string = (
    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)

engine_jumis = create_engine(connection_string)

