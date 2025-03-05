from sqlalchemy import create_engine
from cash_flow.util.Settings import engine_echo

engine = create_engine("sqlite:///../../data/database.db", echo=engine_echo)