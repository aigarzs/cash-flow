from sqlalchemy import select
from sqlalchemy.orm import Session

from cash_flow.database.Model import Document
from cash_flow.database.AEngine import engine

with Session(engine) as session:
    stmt = select(Document).where(Document.id == 2)
    doc = session.scalars(stmt).first()
    amount = doc.amount_LC
    print(f"{type(amount)} : {amount}")