import pandas as pd
from sqlalchemy import text

from cash_flow.database.AEngine import create_engine_db, create_engine_jumis
from cash_flow.database.clearing import clear_all_jumis_disbursements


def sync_documents():
    sync_document_headers()
    sync_document_lines()
    sync_gl_preserved()

def sync_document_headers():
    # ################################################
    # Import all documents from Jumis no Genie
    # ################################################

    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_FinancialDoc"))
        conn.commit()

    page_size = 1000
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                    WITH Jumis_FinancialDoc AS (
                        SELECT 
                            FinancialDocID,
                            FinancialDocNo,
                            DocumentTypeID,
                            FinancialDocDate,
                            DocStatus,
                            DocCurrencyID,
                            DocAmount,
                            PartnerID,
                            DisbursementTerm,
                            Disbursement,
                            DisbursementDate,
                            Comments,
                            DocRegDate,
                            CreateDate,
                            UpdateDate,
                            ROW_NUMBER() OVER (ORDER BY FinancialDocID) AS rn
                        FROM dbo.FinancialDoc
                        )
                    SELECT * FROM Jumis_FinancialDoc
                    WHERE rn BETWEEN :lower AND :upper
                """)

        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                             )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_FinancialDoc", engine_db, if_exists="append", index=False)
            page += 1

    # ################################################
    # Sync all documents from Jumis no Genie
    # ################################################
    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM D01_Documents"))
        conn.commit()
        conn.execute(text("""INSERT INTO D01_Documents 
                          (
                          id,
                          type_id,
                          number,
                          date,
                          date_due,
                          partner_id,
                          description,
                          currency,
                          amount,
                          amount_LC
                          )
                          SELECT 
                          id,
                          type_id,
                          number,
                          date,
                          date_due,
                          partner_id,
                          description,
                          currency,
                          amount,
                          amount_LC                          
                          FROM I01_Import_FinancialDoc
                          """
                          ))
        conn.commit()



def sync_document_lines():
    # ################################################
    # Import all document_line from Jumis no Genie
    # ################################################

    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_FinancialDocLine"))
        conn.commit()

    page_size = 1000
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                    WITH Jumis_FinancialDocLine AS (
                        SELECT 
                            FinancialDocLineID,
                            FinancialDocID,
                            LineDate,
                            CurrencyID,
                            Amount,
                            DebetID,
                            CreditID,
                            Comments,
                            DisbursementDocID,
                            UpdateDate,
                            CreateDate,                          
                            ROW_NUMBER() OVER (ORDER BY FinancialDocLineID) AS rn
                        FROM dbo.FinancialDocLine
                        )
                    SELECT * FROM Jumis_FinancialDocLine
                    WHERE rn BETWEEN :lower AND :upper
                """)

        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                             )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_FinancialDocLine", engine_db, if_exists="append", index=False)
            page += 1

    # return

    # ################################################
    # Sync all gl records from Jumis no Genie
    # ################################################
    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM D03_GeneralLedger"))
        conn.commit()
        conn.execute(text("""INSERT INTO D03_GeneralLedger 
                              (
                                  document_id,
                                  date,
                                  date_due,
                                  partner_id,
                                  entry_type,
                                  account,
                                  currency,
                                  amount,
                                  amount_LC
                              )
                              SELECT 
                                  document_id,
                                  date,
                                  date_due,
                                  partner_id,
                                  entry_type,
                                  account,
                                  currency,
                                  amount,
                                  amount_LC                        
                              FROM I02_Import_FinancialDocLine
                              """
                              ))
        conn.commit()

def sync_gl_preserved():
    engine_db = create_engine_db()
    with engine_db.connect() as conn:
        sql = text("""
        INSERT INTO D03_GeneralLedger_preserved
            (
            document_id,
            partner_id,
            account,
            currency,
            priority,
            void
            )
        SELECT 
            gl.document_id,
            gl.partner_id,
            gl.account,
            gl.currency,
            p.cr_priority,
            p.cr_void
        FROM D03_GeneralLedger AS gl
        LEFT JOIN B02_Accounts AS a 
            ON a.code = gl.account
        LEFT JOIN B04_Partners AS p
            ON p.id = gl.partner_id
        LEFT JOIN D03_GeneralLedger_preserved AS glp 
            ON glp.document_id = gl.document_id AND glp.partner_id = gl.partner_id AND glp.account = gl.account AND glp.currency = gl.currency
        WHERE a.type_id = 2 AND glp.id IS NULL AND gl.entry_type = "CR"
        UNION ALL
        SELECT 
            gl.document_id,
            gl.partner_id,
            gl.account,
            gl.currency,
            p.dr_priority,
            p.dr_void
        FROM D03_GeneralLedger AS gl
        LEFT JOIN B02_Accounts AS a 
            ON a.code = gl.account
        LEFT JOIN B04_Partners AS p
            ON p.id = gl.partner_id
        LEFT JOIN D03_GeneralLedger_preserved AS glp 
            ON glp.document_id = gl.document_id AND glp.partner_id = gl.partner_id AND glp.account = gl.account AND glp.currency = gl.currency
        WHERE a.type_id = 2 AND glp.id IS NULL AND gl.entry_type = "DR"
        """)
        conn.execute(sql)
        conn.commit()

def sync_jummis_disbursement():
    # ################################################
    # Import all disbursement from Jumis no Genie
    # ################################################

    # print("Syncing jumis disbursement")

    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_FinancialDocDisbursement"))
        conn.commit()

    page_size = 1000
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                    WITH Jumis_FinancialDocDisbursement AS (
                        SELECT 
                            FinancialDocDisbursementID,
                            DebetDocID,
                            CreditDocID,
                            DebetAmount,
                            CreditAmount,
                            ROW_NUMBER() OVER (ORDER BY FinancialDocDisbursementID) AS rn
                        FROM dbo.FinancialDocDisbursement
                        )
                    SELECT * FROM Jumis_FinancialDocDisbursement
                    WHERE rn BETWEEN :lower AND :upper
                """)

        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                             )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_FinancialDocDisbursement", engine_db, if_exists="append", index=False)
            page += 1

    clear_all_jumis_disbursements(engine_db)


if __name__ == '__main__':
    # sync_documents()
    # sync_document_headers()
    # sync_document_lines()
    sync_gl_preserved()
    # sync_disbursement()
