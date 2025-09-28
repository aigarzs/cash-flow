from datetime import datetime, timedelta
from random import randint

import pandas as pd
from numpy.random import choice, random
from sqlalchemy import text
from sqlalchemy.orm import Session

from cash_flow.database.AEngine import create_engine_db
from cash_flow.database.Model import Document, Source, DocType, GeneralLedger


def rand_documents():
    engine = create_engine_db()

    with engine.connect() as connection:
        sql = "DELETE FROM D01_Documents"
        connection.execute(text(sql))
        sql = "DELETE FROM D03_GeneralLedger"
        connection.execute(text(sql))
        connection.commit()

    partners = pd.read_sql_table("B04_Partners", engine)

    with Session(engine) as session:
        # DocType.INVOICE_CUSTOMER
        for d in range(1000):
            docdate = datetime(randint(2020, 2025), randint(1, 12), randint(1, 28))
            delta = timedelta(days = randint(1, 31))
            duedate = docdate + delta
            partner = int(choice(partners["id"]))
            amount_excl_vat = round(random() * 10000,2)
            amount_vat = round(amount_excl_vat * 0.21,2)
            account_cr = choice(["6110", "6550"])
            doc = Document(type_id = DocType.INVOICE_CUSTOMER,
                            date = docdate,
                            date_due = duedate,
                            number = d+1,
                            partner_id = partner,
                            description = "Invoice " + str(d+1),
                            currency = "EUR",
                            amount = amount_excl_vat + amount_vat,
                            amount_LC = amount_excl_vat + amount_vat,
                            gl = [
                                GeneralLedger(date = docdate,
                                              entry_type = "CR",
                                              account = account_cr,
                                              currency = "EUR",
                                              partner_id=partner,
                                              amount = amount_excl_vat,
                                              amount_LC = amount_excl_vat
                                ),
                                GeneralLedger(date=docdate,
                                              date_due=duedate,
                                              entry_type="DR",
                                              account="2310",
                                              currency="EUR",
                                              partner_id=partner,
                                              amount=amount_excl_vat+amount_vat,
                                              amount_LC=amount_excl_vat+amount_vat
                                              ),
                                GeneralLedger(date=docdate,
                                              entry_type="CR",
                                              account="5721",
                                              currency="EUR",
                                              partner_id=partner,
                                              amount=amount_vat,
                                              amount_LC=amount_vat
                                              )
                                ] # gl
                           ) # Document

            session.add(doc)
        session.commit()

        # DocType.BANK_RECEIPT
        for d in range(1000):
            docdate = datetime(randint(2020, 2025), randint(1, 12), randint(1, 28))
            partner = int(choice(partners["id"]))
            amount = round(random() * 12100, 2)
            doc = Document(type_id = DocType.BANK_RECEIPT,
                            date = docdate,
                            number = d+1,
                            partner_id = partner,
                            description = "Bank receipt " + str(d + 1),
                            currency = "EUR",
                            amount = amount,
                            amount_LC = amount,
                            gl=[
                                GeneralLedger(date=docdate,
                                              entry_type="CR",
                                              account="2310",
                                              currency="EUR",
                                              partner_id=partner,
                                              amount=amount,
                                              amount_LC=amount
                                              ),
                                GeneralLedger(date=docdate,
                                              entry_type="DR",
                                              account="2620",
                                              currency="EUR",
                                              partner_id=partner,
                                              amount=amount,
                                              amount_LC=amount
                                              ),

                                ] # gl
                           ) # Document

            session.add(doc)
        session.commit()

        # DocType.INVOICE_VENDOR
        for d in range(1000):
            docdate = datetime(randint(2020, 2025), randint(1, 12), randint(1, 28))
            delta = timedelta(days = randint(1, 31))
            duedate = docdate + delta
            partner = int(choice(partners["id"]))
            amount_excl_vat = round(random() * 10000,2)
            amount_vat = round(amount_excl_vat * 0.21,2)
            account_dr = choice(["7110", "7210", "7310", "7510"])
            doc = Document(type_id=DocType.INVOICE_VENDOR,
                           date=docdate,
                           date_due=duedate,
                           number=d + 1,
                           partner_id=partner,
                           description="Invoice " + str(d + 1),
                           currency="EUR",
                           amount=amount_excl_vat + amount_vat,
                           amount_LC=amount_excl_vat + amount_vat,
                           gl=[
                               GeneralLedger(date=docdate,
                                             entry_type="DR",
                                             account=account_dr,
                                             currency="EUR",
                                             partner_id=partner,
                                             amount=amount_excl_vat,
                                             amount_LC=amount_excl_vat
                                             ),
                               GeneralLedger(date=docdate,
                                             date_due=duedate,
                                             entry_type="CR",
                                             account="5310",
                                             currency="EUR",
                                             partner_id=partner,
                                             amount=amount_excl_vat + amount_vat,
                                             amount_LC=amount_excl_vat + amount_vat
                                             ),
                               GeneralLedger(date=docdate,
                                             entry_type="DR",
                                             account="5721",
                                             currency="EUR",
                                             partner_id=partner,
                                             amount=amount_vat,
                                             amount_LC=amount_vat
                                             )
                                ]  # gl
                           )  # Document

            session.add(doc)
        session.commit()

        # DocType.BANK_PAYMENT
        for d in range(1000):
            docdate = datetime(randint(2020, 2025), randint(1, 12), randint(1, 28))
            partner = int(choice(partners["id"]))
            amount = round(random() * 12100, 2)
            doc = Document(type_id=DocType.BANK_PAYMENT,
                           date=docdate,
                           number=d + 1,
                           partner_id=partner,
                           description="Bank payment " + str(d + 1),
                           currency="EUR",
                           amount=amount,
                           amount_LC=amount,
                           gl=[
                               GeneralLedger(date=docdate,
                                             entry_type="DR",
                                             account="5310",
                                             currency="EUR",
                                             partner_id=partner,
                                             amount=amount,
                                             amount_LC=amount
                                             ),
                               GeneralLedger(date=docdate,
                                             entry_type="CR",
                                             account="2620",
                                             currency="EUR",
                                             partner_id=partner,
                                             amount=amount,
                                             amount_LC=amount
                                             ),

                                ]  # gl
                           )  # Document

            session.add(doc)
        session.commit()