from faker import Faker
from sqlalchemy import delete
from sqlalchemy.orm import Session

from cash_flow.database.AEngine import create_engine_db
from cash_flow.database.Model import Currency, AccountType, Account, Source, Partner, DocType


def rand_currencies():
    engine = create_engine_db()

    currencies = [
        ["EUR", "Euro"],
        ["USD", "ASV Dolāri"]
    ]

    with Session(engine) as session:
        stmt = delete(Currency)
        session.execute(stmt)
        session.commit()

        for c in currencies:
            currency = Currency(code=c[0], name=c[1])
            session.add(currency)

        session.commit()


def rand_accounts():
    engine = create_engine_db()

    accounts = [
        ["2610", "Kase", AccountType.BANK_ACCOUNT],
        ["2620", "Banka", AccountType.BANK_ACCOUNT],
        ["2310", "Norēķini ar klientiem", AccountType.CUSTOMERS_ACCOUNT],
        ["5310", "Norēķini ar piegādātājiem", AccountType.VENDORS_ACCOUNT],
        ["6110", "Pārdošanas ieņēmumi", None],
        ["6550", "Citi ieņēmumi", None],
        ["7110", "Izejvielu iegādes", None],
        ["7210", "Ražošanas izmaksas", None],
        ["7310", "Pārdošanas izmaksas", None],
        ["7510", "Citas izmaksas", None],
        ["1210", "Investīcijas pamatlīdzekļos", None],
        ["5721", "PVN", None]
    ]

    with Session(engine) as session:
        stmt = delete(Account)
        session.execute(stmt)
        session.commit()

        for acc in accounts:
            account = Account(code=acc[0], name=acc[1], type_id=acc[2])
            session.add(account)

        session.commit()

def rand_partners():
    engine = create_engine_db()

    fake = Faker()
    Faker.seed(4321)

    with Session(engine) as session:
        stmt = delete(Partner)
        session.execute(stmt)
        session.commit()

        for p in range(100):
            partner = Partner(name=fake.unique.company(),
                                cr_priority=100,
                                dr_priority=100,
                                dr_void = False,
                                cr_void = False,)
            session.add(partner)

        session.commit()

def rand_doctypes():
    engine = create_engine_db()

    dt = [
        [DocType.BANK_RECEIPT, "Ienākošais banka"],
        [DocType.BANK_PAYMENT, "Maksājums banka"],
        [DocType.INVOICE_CUSTOMER, "Rēķins klientam"],
        [DocType.INVOICE_VENDOR, "Rēķins no piegādātāja"],
        [DocType.GL_TRANSACTIONS, "VG grāmatojums"]
    ]

    with Session(engine) as session:
        stmt = delete(DocType)
        session.execute(stmt)
        session.commit()

        for d in dt:
            doctype = DocType(id=d[0], name=d[1])
            session.add(doctype)

        session.commit()