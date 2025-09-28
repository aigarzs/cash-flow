from sqlalchemy.orm import Session

from cash_flow.database.AEngine import create_engine_db
from cash_flow.database.Model import Document, DocType, Reconciliation, Source, GeneralLedger, \
    Account, AccountType, Jumis_FinancialDocDisbursement

from sqlalchemy import select, create_engine, func, text


class ClearingError(Exception):
    pass

def calculate_cleared_amount(engine, entry_id):

    with Session(engine) as session:
        stmt_entry = select(GeneralLedger).where(GeneralLedger.id == entry_id)
        entry = session.scalars(stmt_entry).first()

        if entry:
            if entry.entry_type == "DR":
                stmt_cleared = select(Reconciliation.dr_docid,
                                      func.sum(Reconciliation.amount).label("amount"),
                                      func.max(Reconciliation.date).label("date")
                                      ).where(Reconciliation.dr_docid == entry.document_id,
                                              Reconciliation.account == entry.account,
                                              Reconciliation.currency == entry.currency
                                      ).group_by(Reconciliation.dr_docid)
            elif entry.entry_type == "CR":
                stmt_cleared = select(Reconciliation.cr_docid,
                                      func.sum(Reconciliation.amount).label("amount"),
                                      func.max(Reconciliation.date).label("date")
                                      ).where(Reconciliation.cr_docid == entry.document_id,
                                              Reconciliation.account == entry.account,
                                              Reconciliation.currency == entry.currency
                                              ).group_by(Reconciliation.cr_docid)

            cleared = session.execute(stmt_cleared).first()

            if cleared:
                entry.cleared_amount = round(cleared.amount, 2)
                entry.date_cleared = cleared.date
                if entry.cleared_amount >= entry.amount:
                    entry.cleared = True
                else:
                    entry.cleared = False
            else:
                entry.cleared_amount = 0
                entry.date_cleared = None
                entry.cleared = False

            session.commit()


def calculate_cleared_amount_all(engine):
    with Session(engine) as session:
        stmt_entries = select(GeneralLedger
                              ).join(Account
                              ).where(Account.type_id == AccountType.SETTLEMENT_ACCOUNT)
        entries = session.scalars(stmt_entries).all()
        for entry in entries:
            calculate_cleared_amount(engine, entry.id)

def calculate_cleared_amount_all_uncleared(engine):
    with Session(engine) as session:
        stmt_entries = select(GeneralLedger
                              ).join(Account
                              ).where(Account.type_id == AccountType.SETTLEMENT_ACCOUNT,
                                      GeneralLedger.cleared == False)
        entries = session.scalars(stmt_entries).all()
        for entry in entries:
            calculate_cleared_amount(engine, entry.id)



def clear(engine, account, currency, cr_docid, dr_docid, amount=0):

    stmt_cr_gl = (select(GeneralLedger.id,
                         GeneralLedger.amount,
                         GeneralLedger.cleared_amount,
                         GeneralLedger.date)
                        .join(Account)
                        .where(GeneralLedger.document_id == cr_docid,
                                GeneralLedger.cleared == False,
                                GeneralLedger.currency == currency,
                                GeneralLedger.entry_type == "CR",
                                GeneralLedger.account == account,
                                Account.type_id == AccountType.SETTLEMENT_ACCOUNT,
                            )
                       )
    stmt_dr_gl = (select(GeneralLedger.id,
                         GeneralLedger.amount,
                         GeneralLedger.cleared_amount,
                         GeneralLedger.date)
                       .join(Account)
                       .where(GeneralLedger.document_id == dr_docid,
                              GeneralLedger.cleared == False,
                              GeneralLedger.currency == currency,
                              GeneralLedger.entry_type == "DR",
                              GeneralLedger.account == account,
                              Account.type_id == AccountType.SETTLEMENT_ACCOUNT,
                              )
                       )

    with Session(engine) as session:

        cr_entry = session.execute(stmt_cr_gl).first()
        dr_entry = session.execute(stmt_dr_gl).first()

        # print(f"cr_entry: {cr_entry}\ndr_entry: {dr_entry}")
        if cr_entry and dr_entry:

            cr_uncleared = round(cr_entry.amount - cr_entry.cleared_amount,2)
            dr_uncleared = round(dr_entry.amount - dr_entry.cleared_amount,2)

            if amount > 0:
                amount = min(amount, cr_uncleared, dr_uncleared)
            else:
                amount = min(cr_uncleared, dr_uncleared)

            date = max(dr_entry.date, cr_entry.date)

            print(f"Reconciliation {date}: cr:{cr_docid} dr:{dr_docid} amount:{currency} {amount}")
            reconciliation = Reconciliation(date=date,
                                            account=account,
                                            currency=currency,
                                            amount=amount,
                                            cr_docid=cr_docid,
                                            dr_docid=dr_docid,
                                            )
            session.add(reconciliation)
            session.commit()

            calculate_cleared_amount(engine, cr_entry.id)
            calculate_cleared_amount(engine, dr_entry.id)


def clear_auto_partner(engine, account, partner_id, currency):
    stmt_cr_glentry = (select(GeneralLedger.id,
                              GeneralLedger.document_id,
                              GeneralLedger.cleared_amount,
                              GeneralLedger.account,
                              Account.type_id.label("account_type"),
                              GeneralLedger.amount,
                              GeneralLedger.currency,
                              GeneralLedger.date,
                              GeneralLedger.partner_id
                              )
                       .join(Account)
                       .where(GeneralLedger.cleared == False,
                              GeneralLedger.entry_type == "CR",
                              GeneralLedger.account == account,
                              Account.type_id == AccountType.SETTLEMENT_ACCOUNT,
                              GeneralLedger.currency == currency,
                              GeneralLedger.partner_id == partner_id,
                              )
                       .order_by(GeneralLedger.date, GeneralLedger.document_id, GeneralLedger.id)
                       )

    stmt_dr_glentry = (select(GeneralLedger.id,
                              GeneralLedger.document_id,
                              GeneralLedger.cleared_amount,
                              GeneralLedger.account,
                              Account.type_id.label("account_type"),
                              GeneralLedger.amount,
                              GeneralLedger.currency,
                              GeneralLedger.date,
                              GeneralLedger.partner_id
                              )
                       .join(Account)
                       .where(GeneralLedger.cleared == False,
                              GeneralLedger.entry_type == "DR",
                              GeneralLedger.account == account,
                              Account.type_id == AccountType.SETTLEMENT_ACCOUNT,
                              GeneralLedger.currency == currency,
                              GeneralLedger.partner_id == partner_id,
                              )
                       .order_by(GeneralLedger.date, GeneralLedger.document_id, GeneralLedger.id)
                       )

    with Session(engine) as session:

        while True:
            dr = session.execute(stmt_dr_glentry).first()
            cr = session.execute(stmt_cr_glentry).first()

            if dr and cr:
                dr_uncleared = round(dr.amount - dr.cleared_amount, 2)
                cr_uncleared = round(cr.amount - cr.cleared_amount, 2)
                amount = min(dr_uncleared, cr_uncleared)
                clear(engine, account, currency, cr.document_id, dr.document_id, amount)
            else:
                break

def clear_auto_account(engine, account):
    stmt_partners = (select(GeneralLedger.account,
                            GeneralLedger.partner_id,
                            GeneralLedger.currency
                            )
                        .join(Account)
                        .where(GeneralLedger.account == account,
                               GeneralLedger.cleared == False,
                                Account.type_id == AccountType.SETTLEMENT_ACCOUNT)
                        .group_by(GeneralLedger.account,
                                  GeneralLedger.partner_id,
                                  GeneralLedger.currency)
                    )

    with Session(engine) as session:
        partners = session.execute(stmt_partners).fetchall()
        for partner in partners:
            clear_auto_partner(engine, account, partner.partner_id, partner.currency)


def clear_auto_all_accounts(engine):
    stmt_accounts = (select(GeneralLedger.account)
                     .join(Account)
                     .where(GeneralLedger.cleared == False,
                            Account.type_id == AccountType.SETTLEMENT_ACCOUNT)
                     .group_by(GeneralLedger.account)
                     )

    with Session(engine) as session:
        accounts = session.execute(stmt_accounts).fetchall()
        for account in accounts:
            clear_auto_account(engine, account.account)

def delete_all_reconciliations(engine):
    with engine.connect() as conn:
        sql = text("DELETE FROM " + Reconciliation.__tablename__ )
        conn.execute(sql)
        conn.commit()
        sql = text("UPDATE " + GeneralLedger.__tablename__ + " SET cleared = false, cleared_amount = 0")
        conn.execute(sql)
        conn.commit()

def clear_jumis_disbursement(engine, disbursement_id):
    # Jumis has DebetDocID for invoices and CreditDocID for bank,
    # No matter if those are DB invoices or CR invoices
    # print(f"Clearing jumis disbursement {disbursement_id}")

    stmt_disbursements = (select(Jumis_FinancialDocDisbursement.CreditDocID,
                                 Jumis_FinancialDocDisbursement.DebetDocID,
                                 Jumis_FinancialDocDisbursement.CreditAmount,
                                 Jumis_FinancialDocDisbursement.DebetAmount)
                                .where(Jumis_FinancialDocDisbursement.FinancialDocDisbursementID == disbursement_id)
                                )

    with Session(engine) as session:
        disb = session.execute(stmt_disbursements).first()

        stmt_disbursement_invoices = (select(GeneralLedger.document_id,
                                       GeneralLedger.entry_type,
                                       GeneralLedger.account,
                                       GeneralLedger.currency)
                         .join(Account)
                         .where(GeneralLedger.cleared == False,
                                Account.type_id == AccountType.SETTLEMENT_ACCOUNT,
                                GeneralLedger.document_id == disb.DebetDocID))

        invoice_entries = session.execute(stmt_disbursement_invoices).fetchall()

        for invoice in invoice_entries:
            amount = min(disb.CreditAmount, disb.DebetAmount)

            if invoice.entry_type == "DR":
                db_docid = disb.DebetDocID
                cr_docid = disb.CreditDocID
            else:
                db_docid = disb.CreditDocID
                cr_docid = disb.DebetDocID

            clear(engine, invoice.account, invoice.currency, cr_docid, db_docid, amount)

def clear_all_jumis_disbursements(engine):
    # print("Clearing all jumis disbursement")

    stmt_disbursements = (select(Jumis_FinancialDocDisbursement.FinancialDocDisbursementID)
                            .order_by(Jumis_FinancialDocDisbursement.FinancialDocDisbursementID)
                          )

    with Session(engine) as session:
        disbursements = session.execute(stmt_disbursements).fetchall()
        for disb in disbursements:
            clear_jumis_disbursement(engine, disb.FinancialDocDisbursementID)


if __name__ == "__main__":
    engine = create_engine_db()
    delete_all_reconciliations(engine)

    # clear_auto_account(engine, "2310")
    clear_auto_all_accounts(engine)

    # calculate_cleared_amount_all(engine)

    # clear_all_jumis_disbursements(engine)