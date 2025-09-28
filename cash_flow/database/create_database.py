from random import randint, random, choice
from datetime import datetime, timedelta


from faker import Faker
from sqlalchemy.orm import Session

from cash_flow.database.AEngine import create_engine_db
from cash_flow.database.Model import Base, AccountType, Account, \
    Source, Currency, Document, DocType, GeneralLedger
from cash_flow.database.Views import views_all
from cash_flow.database.clearing import clear_auto_all_accounts, delete_all_reconciliations
from cash_flow.database.rand_dimensions import rand_partners, rand_accounts, rand_currencies, rand_doctypes
from cash_flow.database.rand_documents import rand_documents
from cash_flow.database.sync_dimensions import sync_accounts, sync_currencies, sync_partners, sync_doctypes, \
    sync_currencyrates
from cash_flow.database.sync_documents import sync_documents, sync_document_lines, \
    sync_document_headers, sync_jummis_disbursement


def create_tables():
    engine = create_engine_db()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def create_views():
    engine = create_engine_db()
    views_all(engine.connect())

def create_dimensions_data():
    # rand_accounts()
    sync_accounts()
    # rand_currencies()
    sync_currencies()
    sync_currencyrates()
    # rand_doctypes()
    sync_doctypes()
    # rand_partners()
    sync_partners()


def create_documents_data():
    sync_documents()
    # rand_documents()

def create_clearings_data():
    engine = create_engine_db()
    # pass
    delete_all_reconciliations(engine)
    sync_jummis_disbursement()
    clear_auto_all_accounts(engine)


if __name__ == '__main__':
    # create_tables()
    # create_views()
    create_dimensions_data()
    create_documents_data()
    create_clearings_data()
    # clear_auto_all_customers()
    # clear_auto_all_vendors()