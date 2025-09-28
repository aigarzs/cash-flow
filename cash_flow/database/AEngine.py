from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Source
from cash_flow.util.Settings import engine_echo

def create_engine_db():
    engine_db = create_engine("sqlite:///../../data/database.db", echo=engine_echo)
    return engine_db

def create_engine_jumis():
    engine_db = create_engine_db()

    with Session(engine_db) as session:
        stmt = select(Source).where(Source.id == 2)
        jumis = session.scalars(stmt).first()

        username = jumis.username
        password = jumis.password
        url = jumis.url
        database = jumis.database

    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{url}/{database}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

    engine_jumis = create_engine(connection_string, echo=engine_echo)
    return engine_jumis
