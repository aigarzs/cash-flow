from locale import currency

from sqlalchemy.orm import Session

from cash_flow.database.AEngine import engine_db as engine
from cash_flow.database.Model import Document, DocType, Reconciliation, Source

from sqlalchemy import select, create_engine, func



class ClearingError(Exception):
    pass


def calculate_cleared_amount(document_id):
    with (Session(engine) as session):
        stmt_document = select(Document).where(Document.id == document_id)
        document = session.scalars(stmt_document).first()
        if document:
            if document.type_id in [DocType.INVOICE_CUSTOMER, DocType.INVOICE_VENDOR, DocType.PAYROLL]:
                stmt_cleared = select(Reconciliation.invoice_id,
                                      func.sum(Reconciliation.amount).label("amount"),
                                      func.max(Reconciliation.date).label("date")
                                        ).where(Reconciliation.invoice_id == document_id,
                                        Reconciliation.currency == document.currency
                                        ).group_by(Reconciliation.invoice_id)
            elif document.type_id in [DocType.CREDITNOTE_CUSTOMER, DocType.CREDITNOTE_VENDOR, DocType.BANK_RECEIPT, DocType.BANK_PAYMENT]:
                stmt_cleared = select(Reconciliation.invoice_id,
                                      func.sum(Reconciliation.amount).label("amount"),
                                      func.max(Reconciliation.date).label("date")
                                      ).where(Reconciliation.payment_id == document_id,
                                              Reconciliation.currency == document.currency
                                              ).group_by(Reconciliation.payment_id)

            cleared = session.execute(stmt_cleared).first()
            if cleared:
                document.cleared_amount = round(cleared[1],2)
                document.date_cleared = cleared[2]
                if document.cleared_amount >= document.amount:
                    document.cleared = True
                else:
                    document.cleared = False
            else:
                document.cleared_amount = 0
                document.date_cleared = None
                document.cleared = False


            session.commit()


def calculate_cleared_amount_all():
    with (Session(engine) as session):
        stmt_documents = select(Document)
        documents = session.scalars(stmt_documents).all()
        for doc in documents:
            calculate_cleared_amount(doc.id)



def clear(source, source_key, invoice_id, payment_id, amount=0):

    stmt_invoice = select(Document).where(Document.id == invoice_id, Document.cleared == False)
    stmt_payment = select(Document).where(Document.id == payment_id, Document.cleared == False)

    with Session(engine) as session:

        invoice = session.scalars(stmt_invoice).first()
        payment = session.scalars(stmt_payment).first()

        if invoice and payment:

            invoice_uncleared = round(invoice.amount - invoice.cleared_amount,2)
            payment_uncleared = round(payment.amount - payment.cleared_amount,2)

            if amount > 0:
                amount = min(amount, invoice_uncleared, payment_uncleared)
            else:
                amount = min(invoice_uncleared, payment_uncleared)

            date = max(invoice.date, payment.date)

            if (invoice.type_id == DocType.INVOICE_CUSTOMER and
                payment.type_id in (DocType.BANK_RECEIPT, DocType.CREDITNOTE_CUSTOMER) and
                invoice.currency == payment.currency):

                reconciliation = Reconciliation(amount=amount, currency=invoice.currency, date=date, invoice_id=invoice_id,
                                                payment_id=payment_id, source_id=source, source_key=source_key)
                session.add(reconciliation)

            elif (invoice.type_id in (DocType.INVOICE_VENDOR, DocType.PAYROLL) and
                payment.type_id in (DocType.BANK_PAYMENT, DocType.CREDITNOTE_VENDOR) and
                invoice.currency == payment.currency):

                reconciliation = Reconciliation(amount=amount, currency=invoice.currency, date=date, invoice_id=invoice_id,
                                                payment_id=payment_id, source_id=source, source_key=source_key)
                session.add(reconciliation)

        session.commit()

    calculate_cleared_amount(invoice_id)
    calculate_cleared_amount(payment_id)

def clear_auto_customer(customer_id):
    with Session(engine) as session:
        stmt_invoice = select(Document) \
            .where(Document.customer_id == customer_id,
                   Document.type_id == DocType.INVOICE_CUSTOMER,
                   Document.cleared == False) \
            .order_by(Document.date)
        stmt_payment = select(Document) \
            .where(Document.customer_id == customer_id,
                   Document.type_id.in_([DocType.CREDITNOTE_CUSTOMER, DocType.BANK_RECEIPT]),
                   Document.cleared == False) \
            .order_by(Document.date)
        while True:
            invoice = session.scalars(stmt_invoice).first()
            payment = session.scalars(stmt_payment).first()
            if not (invoice and payment):
                break
            clear(Source.GENIE, "1", invoice.id, payment.id)

def clear_auto_vendor(vendor_id):
    with Session(engine) as session:
        stmt_invoice = select(Document) \
            .where(Document.vendor_id == vendor_id,
                   Document.type_id.in_([DocType.INVOICE_VENDOR, DocType.PAYROLL]),
                   Document.cleared == False) \
            .order_by(Document.date)
        stmt_payment = select(Document) \
            .where(Document.vendor_id == vendor_id,
                   Document.type_id.in_([DocType.CREDITNOTE_VENDOR, DocType.BANK_PAYMENT]),
                   Document.cleared == False) \
            .order_by(Document.date)
        while True:
            invoice = session.scalars(stmt_invoice).first()
            payment = session.scalars(stmt_payment).first()
            if not (invoice and payment):
                break
            clear(Source.GENIE, "1", invoice.id, payment.id)

def clear_auto_all_customers():
    with Session(engine) as session:
        stmt_customers = select(Document.customer_id).group_by(Document.customer_id)
        customers = session.execute(stmt_customers).fetchall()
        for c in customers:
            clear_auto_customer(c[0])

def clear_auto_all_vendors():
    with Session(engine) as session:
        stmt_vendors = select(Document.vendor_id).group_by(Document.vendor_id)
        vendors = session.execute(stmt_vendors).fetchall()
        for v in vendors:
            clear_auto_vendor(v[0])


if __name__ == "__main__":
    # clear(Sources.DEFAULT, "1", 399, 652)
    # calculate_cleared_amount(575)
    # clear_auto_customer(2)
    # clear_auto_all_customers()
    # clear_auto_all_vendors()
    calculate_cleared_amount_all()