from random import randint, random, choice
from decimal import Decimal, getcontext as deccontext
from datetime import datetime, timedelta


from faker import Faker
from sqlalchemy.orm import Session

from cash_flow.database.AEngine import engine_db as engine
from cash_flow.database.Model import Base, AccountType, Account, \
    Source, Currency, Customer, Vendor, Document, DocType, GeneralLedger
from cash_flow.database.Views import views_all
from cash_flow.gl.clearing import clear_auto_all_customers, clear_auto_all_vendors


def test_create_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    views_all(engine.connect())



def test_create_dimensions_data():

    currencies = [
        ["EUR", "Euro"],
        ["USD", "ASV Dolāri"]
    ]
    accounts = [
        ["2610", "Kase", AccountType.BANK_ACCOUNT],
        ["2620", "Banka", AccountType.BANK_ACCOUNT],
        ["2310", "Norēķini ar klientiem", AccountType.CUSTOMERS_ACCOUNT],
        ["5310", "Norēķini ar piegādātājiem", AccountType.VENDORS_ACCOUNT],
        ["6110", "Pārdošanas ieņēmumi", AccountType.REVENUES_ACCOUNT],
        ["6550", "Citi ieņēmumi", AccountType.REVENUES_ACCOUNT],
        ["7110", "Izejvielu iegādes", AccountType.EXPENSES_ACCOUNT],
        ["7210", "Ražošanas izmaksas", AccountType.EXPENSES_ACCOUNT],
        ["7310", "Pārdošanas izmaksas", AccountType.EXPENSES_ACCOUNT],
        ["7510", "Citas izmaksas", AccountType.EXPENSES_ACCOUNT],
        ["1210", "Investīcijas pamatlīdzekļos", AccountType.EXPENSES_ACCOUNT],
        ["5721", "PVN", AccountType.TAX_ACCOUNT]

    ]

    with Session(engine) as session:
        for c in currencies:
            currency = Currency(code = c[0], name = c[1])
            session.add(currency)

        for acc in accounts:
            account = Account(code = acc[0], name = acc[1], type_id = acc[2])
            session.add(account)

        fake = Faker()
        Faker.seed(4321)
        for c in range(100):
            customer = Customer(name = fake.unique.company(),
                                 source_id = Source.DEFAULT,
                                 source_key = c+100,
                                 priority = 100)
            session.add(customer)

        for v in range(100):
            vendor = Vendor(name = fake.unique.company(),
                                 source_id = Source.DEFAULT,
                                 source_key = v+100,
                                 priority = 100)
            session.add(vendor)

        session.commit()



def test_create_documents_data():

    with Session(engine) as session:
        for d in range(1500):
            docdate = datetime(randint(2020, 2025), randint(1, 12), randint(1, 28))
            delta = timedelta(days = randint(1, 31))
            duedate = docdate + delta
            customer = randint(1,100)
            amount_excl_vat = round(random() * 10000,2)
            amount_vat = round(amount_excl_vat * 0.21,2)
            account_cr = choice(["6110", "6550"])
            doc = Document(source_id = Source.DEFAULT,
                            source_key = d+1,
                            type_id = DocType.INVOICE_CUSTOMER,
                            date = docdate,
                            date_due = duedate,
                            date_planned_clearing = duedate,
                            priority = 100,
                            number = d+1,
                            customer_id = customer,
                            description = "Invoice " + str(d+1),
                            amount = round(amount_excl_vat + amount_vat,2),
                            currency = "EUR",
                            amount_LC = round(amount_excl_vat + amount_vat,2),
                            gl = [
                                GeneralLedger(entry_type = "CR",
                                              account = account_cr,
                                              amount = amount_excl_vat,
                                              amount_LC = amount_excl_vat),
                                GeneralLedger(entry_type = "DR",
                                              account = "2310",
                                              amount = amount_excl_vat,
                                              amount_LC = amount_excl_vat),
                                GeneralLedger(entry_type = "CR",
                                              account = "5721",
                                              amount = amount_vat,
                                              amount_LC = amount_vat),
                                GeneralLedger(entry_type = "DR",
                                              account = "2310",
                                              amount = amount_vat,
                                              amount_LC = amount_vat)
                            ])
            session.add(doc)

        for d in range(1000):
            docdate = datetime(randint(2020, 2025), randint(1, 12),
                               randint(1, 28))
            customer = randint(1, 100)
            amount = round(random() * 10000, 2)
            doc = Document(source_id=Source.DEFAULT,
                            source_key=d+1001,
                            type_id=DocType.BANK_RECEIPT,
                            date=docdate,
                            date_due=docdate,
                            date_planned_clearing=docdate,
                            priority=100,
                            number=d+1001,
                            customer_id=customer,
                            description="Payment " + str(d+1001),
                            amount=amount,
                            currency="EUR",
                            amount_LC=amount,
                            gl=[
                                GeneralLedger(entry_type = "CR",
                                              account = "2310",
                                              amount = amount,
                                              amount_LC = amount),
                                GeneralLedger(entry_type = "DR",
                                              account="2620",
                                              amount=amount,
                                              amount_LC=amount)
                            ])
            session.add(doc)

        for d in range(300):
            docdate = datetime(randint(2020, 2025), randint(1, 12),
                               randint(1, 28))
            customer = randint(1, 100)
            amount_excl_vat = round(random() * 10000, 2)
            amount_vat = round(amount_excl_vat * 0.21, 2)
            account_dr = choice(["6110", "6550"])
            doc = Document(source_id=Source.DEFAULT,
                            source_key=d+2501,
                            type_id=DocType.CREDITNOTE_CUSTOMER,
                            date=docdate,
                            date_due=docdate,
                            date_planned_clearing=docdate,
                            priority=100,
                            number=d+2501,
                            customer_id=customer,
                            description="Credit note " + str(d+2501),
                            amount=round(amount_excl_vat + amount_vat, 2),
                            currency="EUR",
                            amount_LC=round(amount_excl_vat + amount_vat, 2),
                            gl=[
                                GeneralLedger(entry_type = "CR",
                                              account = "2310",
                                              amount = amount_excl_vat,
                                              amount_LC = amount_excl_vat),
                                GeneralLedger(entry_type = "DR",
                                              account = account_dr,
                                              amount = amount_excl_vat,
                                              amount_LC = amount_excl_vat),
                                GeneralLedger(entry_type = "CR",
                                              account = "2310",
                                              amount = amount_vat,
                                              amount_LC = amount_vat),
                                GeneralLedger(entry_type = "DR",
                                              account="5721",
                                              amount=amount_vat,
                                              amount_LC=amount_vat),
                            ])
            session.add(doc)



        for d in range(1500):
            docdate = datetime(randint(2020, 2025), randint(1, 12), randint(1, 28))
            delta = timedelta(days=randint(1, 31))
            duedate = docdate + delta
            vendor = randint(1, 100)
            amount_excl_vat = round(random() * 10000, 2)
            amount_vat = round(amount_excl_vat * 0.21, 2)
            account_dr = choice(["7110", "7210", "7310", "7510"])
            doc = Document(source_id=Source.DEFAULT,
                           source_key=d + 2001,
                           type_id=DocType.INVOICE_VENDOR,
                           date=docdate,
                           date_due=duedate,
                           date_planned_clearing=duedate,
                           priority=100,
                           number=d + 2001,
                           vendor_id=vendor,
                           description="Invoice " + str(d + 2001),
                           amount=round(amount_excl_vat + amount_vat, 2),
                           currency="EUR",
                           amount_LC=round(amount_excl_vat + amount_vat, 2),
                           gl=[
                               GeneralLedger(entry_type = "CR",
                                             account = "5310",
                                             amount = amount_excl_vat,
                                             amount_LC = amount_excl_vat),
                               GeneralLedger(entry_type = "DR",
                                             account = account_dr,
                                             amount=amount_excl_vat,
                                             amount_LC=amount_excl_vat),
                               GeneralLedger(entry_type = "CR",
                                             account = "5310",
                                             amount = amount_vat,
                                             amount_LC = amount_vat),
                               GeneralLedger(entry_type = "DR",
                                             account = "5721",
                                             amount=amount_vat,
                                             amount_LC=amount_vat)
                           ])
            session.add(doc)

        for d in range(1000):
            docdate = datetime(randint(2020, 2025), randint(1, 12),
                               randint(1, 28))
            vendor = randint(1, 100)
            amount = round(random() * 10000, 2)
            doc = Document(source_id=Source.DEFAULT,
                           source_key=d + 3001,
                           type_id=DocType.BANK_PAYMENT,
                           date=docdate,
                           date_due=docdate,
                           date_planned_clearing=docdate,
                           priority=100,
                           number=d + 3001,
                           vendor_id=vendor,
                           description="Payment " + str(d + 3001),
                           amount=amount,
                           currency="EUR",
                           amount_LC=amount,
                           gl=[
                               GeneralLedger(entry_type = "CR",
                                             account = "2620",
                                             amount = amount,
                                             amount_LC = amount),
                               GeneralLedger(entry_type = "DR",
                                             account="5310",
                                             amount=amount,
                                             amount_LC=amount)
                           ])
            session.add(doc)

        for d in range(300):
            docdate = datetime(randint(2020, 2025), randint(1, 12),
                               randint(1, 28))
            vendor = randint(1, 100)
            amount_excl_vat = round(random() * 10000, 2)
            amount_vat = round(amount_excl_vat * 0.21, 2)
            account_cr = choice(["7110", "7210", "7310", "7510"])
            doc = Document(source_id=Source.DEFAULT,
                           source_key=d + 3501,
                           type_id=DocType.CREDITNOTE_VENDOR,
                           date=docdate,
                           date_due=docdate,
                           date_planned_clearing=docdate,
                           priority=100,
                           number=d + 2501,
                           vendor_id=vendor,
                           description="Credit note " + str(d + 3501),
                           amount=round(amount_excl_vat + amount_vat, 2),
                           currency="EUR",
                           amount_LC=round(amount_excl_vat + amount_vat, 2),
                           gl=[
                               GeneralLedger(entry_type = "CR",
                                             account = account_cr,
                                             amount = amount_excl_vat,
                                             amount_LC = amount_excl_vat),
                               GeneralLedger(entry_type = "DR",
                                             account="5310",
                                             amount=amount_excl_vat,
                                             amount_LC=amount_excl_vat),
                               GeneralLedger(entry_type = "CR",
                                             account = "5721",
                                             amount = amount_vat,
                                             amount_LC = amount_vat),
                               GeneralLedger(entry_type = "DR",
                                             account="5310",
                                             amount=amount_vat,
                                             amount_LC=amount_vat),
                           ])
            session.add(doc)

        session.commit()



test_create_database()
test_create_dimensions_data()
test_create_documents_data()
# clear_auto_all_customers()
# clear_auto_all_vendors()