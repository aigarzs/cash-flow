from sqlalchemy import text
from cash_flow.database.AEngine import create_engine_db
import inspect
import sys

from cash_flow.util.log import get_logger

logger = get_logger("Views")

def views_all(connection):

    current_module = sys.modules[__name__]
    current_function = inspect.currentframe().f_code.co_name

    functions = inspect.getmembers(current_module, inspect.isfunction)
    for name, function in functions:
        if name not in [current_function, "create_engine_db", "text"]:
            # print(name)
            function(connection)

def view_general_ledger(connection):
    logger.info("Updating view G00_GeneralLedger")
    drop = "DROP VIEW IF EXISTS G00_GeneralLedger"
    create = """CREATE VIEW G00_GeneralLedger AS
            SELECT 
                gl.*,
                p.date_planned_clearing,
                p.memo,
                p.priority,
                p.void
    
            FROM D03_GeneralLedger AS gl
            LEFT JOIN D03_GeneralLedger_preserved AS p
                ON gl.account = p.account AND 
                gl.currency = p.currency AND
                 gl.document_id = p.document_id AND
                 gl.partner_id = p.partner_id
    
    """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_cash_transactions(connection):
    logger.info("Updating view G01_CashTransactions")
    drop = "DROP VIEW IF EXISTS G01_CashTransactions"
    create = """CREATE VIEW G01_CashTransactions AS
                SELECT 
                            gl.id AS id,
                            gl.document_id AS d_id,
                            dt.name AS d_type,
                            d.number AS d_number, 
                            d.description AS d_description,
                            gl.date AS date,
                            IIF(gl.entry_type = "DR", "Receipt", "Payment") AS cash_type,
                            d.partner_id AS partner_id,
                            p.name AS partner_name,
                            gl.currency AS currency,
                            gl.entry_type AS entry_type,
                            gl.account AS account,
                            gl.amount  AS amount,
                            gl.amount_LC AS amount_LC
                                                        
                        FROM B02_Accounts AS a 
                        LEFT JOIN D03_GeneralLedger AS gl ON a.code = gl.account
                        LEFT JOIN D01_Documents AS d ON gl.document_id = d.id
                        LEFT JOIN D02_DocTypes AS dt ON d.type_id = dt.id
                        LEFT JOIN B04_Partners AS p ON d.partner_id = p.id
                        WHERE a.type_id = 1 AND gl.id IS NOT NULL
                        ORDER BY gl.date, gl.document_id
        """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_generalledger(connection):
    logger.info("Updating view G02_Cash_GeneralLedger")
    drop = "DROP VIEW IF EXISTS G02_Cash_GeneralLedger"
    create = """CREATE VIEW G02_Cash_GeneralLedger AS
            SELECT 
                            gl.id AS id,
                            gl.document_id AS d_id,
                            cash.cash_type AS cash_type,
                            cash.d_type AS d_type,
                            cash.d_number AS d_number,
                            gl.date AS date,
                            cash.partner_id AS partner_id,
                            cash.partner_name AS partner_name,
                            cash.d_description AS d_description, 
                            gl.currency AS currency,
                            gl.entry_type AS entry_type,
                            gl.account AS account,
                            gl.amount AS amount,
                            gl.amount_LC AS amount_LC
                             
            FROM G01_CashTransactions AS cash 
            LEFT JOIN D03_GeneralLedger AS gl
            ON cash.d_id = gl.document_id
            ORDER BY gl.date, gl.document_id
            """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_corresponding(connection):
    logger.info("Updating view G03_CashTransactions_Corresponding")
    drop = "DROP VIEW IF EXISTS G03_CashTransactions_Corresponding"
    create = """CREATE VIEW G03_CashTransactions_Corresponding AS
            SELECT 
                    gl.id AS id,
                    cash.d_id AS d_id,
                    cash.d_type AS d_type,
                    cash.d_number AS d_number, 
                    cash.date AS date,
                    cash.d_description AS d_description,
                    cash.partner_id AS partner_id,
                    cash.partner_name AS partner_name,
                    cash.currency AS currency,
                    cash.cash_type AS cash_type,
                    gl.entry_type AS entry_type,
                    gl.account AS account,
                    a.type_id AS account_type,
                    gl.amount AS amount,
                    gl.amount_LC AS amount_LC,
                    gl.cleared_amount AS cleared_amount,
                    gl.date_cleared AS date_cleared,
                    gl.cleared AS cleared
                FROM G01_CashTransactions AS cash 
                LEFT JOIN D03_GeneralLedger AS gl 
                ON cash.d_id = gl.document_id AND cash.id <> gl.id
                LEFT JOIN B02_Accounts AS a ON gl.account = a.code
                ORDER BY cash.date, cash.d_id
            """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_reconciliations(connection):
    logger.info("Updating view G04_CashTransactions_Reconciliations_CR")
    logger.info("Updating view G04_CashTransactions_Reconciliations_DR")
    drop_cr = "DROP VIEW IF EXISTS G04_CashTransactions_Reconciliations_CR"
    drop_dr = "DROP VIEW IF EXISTS G04_CashTransactions_Reconciliations_DR"
    create_cr = """CREATE VIEW G04_CashTransactions_Reconciliations_CR AS
            SELECT 
                    cash.id AS id,
                    cash.d_id AS d_id, 
                    cash.currency AS currency,
                    cash.cash_type AS cash_type,
                    cash.entry_type AS entry_type,
                    cash.account AS account,
                    cash.account_type AS account_type,
                    cash.amount AS amount,
                    cash.amount_LC AS amount_LC,
                    r.id AS r_id,
                    r.amount AS r_amount,
                    corr.id AS corr_id,
                    corr.document_id AS corr_d_id,
                    corr.entry_type AS corr_entry_type,
                    corr.amount AS corr_amount,
                    corr.amount_LC AS corr_amount_LC,
                    IIF(corr.amount <> 0, r.amount / corr.amount, 0) AS r_rate
                
                FROM G03_CashTransactions_Corresponding AS cash
                LEFT JOIN D04_Reconciliations AS r
                ON cash.account_type IN (2, 3) AND cash.entry_type = "CR" AND cash.account = r.account AND cash.currency = r.currency AND cash.d_id = r.cr_docid 
                LEFT JOIN D03_GeneralLedger AS corr 
                ON corr.account = r.account AND corr.entry_type = "DR" AND corr.currency = r.currency AND corr.document_id = r.dr_docid
                WHERE r.id IS NOT NULL
            """
    create_dr = """CREATE VIEW G04_CashTransactions_Reconciliations_DR AS
                SELECT 
                    cash.id AS id,
                    cash.d_id AS d_id, 
                    cash.currency AS currency,
                    cash.cash_type AS cash_type,
                    cash.entry_type AS entry_type,
                    cash.account AS account,
                    cash.account_type AS account_type,
                    cash.amount AS amount,
                    cash.amount_LC AS amount_LC,
                    r.id AS r_id,
                    r.amount AS r_amount,
                    corr.id AS corr_id,
                    corr.document_id AS corr_d_id,
                    corr.entry_type AS corr_entry_type,
                    corr.amount AS corr_amount,
                    corr.amount_LC AS corr_amount_LC,
                    IIF(corr.amount <> 0, r.amount / corr.amount, 0) AS r_rate
                
                FROM G03_CashTransactions_Corresponding AS cash
                LEFT JOIN D04_Reconciliations AS r
                ON cash.account_type IN (2, 3) AND cash.entry_type = "DR" AND cash.account = r.account AND cash.currency = r.currency AND cash.d_id = r.dr_docid 
                LEFT JOIN D03_GeneralLedger AS corr 
                ON corr.account = r.account AND corr.entry_type = "CR" AND corr.currency = r.currency AND corr.document_id = r.cr_docid
                WHERE r.id IS NOT NULL
                """

    connection.execute(text(drop_cr))
    connection.execute(text(drop_dr))
    connection.execute(text(create_cr))
    connection.execute(text(create_dr))

def view_cash_reconciled(connection):
    logger.info("Updating view G05_CashTransactions_Reconciled_CR")
    logger.info("Updating view G05_CashTransactions_Reconciled_DR")
    drop_cr = "DROP VIEW IF EXISTS G05_CashTransactions_Reconciled_CR"
    drop_dr = "DROP VIEW IF EXISTS G05_CashTransactions_Reconciled_DR"
    create_cr = """CREATE VIEW G05_CashTransactions_Reconciled_CR AS
            SELECT
                    r.id AS id,
                    r.d_id AS d_id,
                    r.cash_type AS cash_type,
                    r.entry_type AS entry_type,
                    r.account AS account,
                    r.currency AS currency,
                    r.amount AS amount,
                    r.amount_LC AS amount_LC,
                    corr.id AS corr_id,
                    corr.document_id AS corr_d_id,
                    corr.entry_type AS corr_entry_type,
                    corr.account AS corr_account,
                    r.r_rate * corr.amount AS corr_projected_amount,
                    r.r_rate * corr.amount_LC AS corr_projected_amount_LC
                    
                    
            FROM G04_CashTransactions_Reconciliations_CR AS r
            LEFT JOIN D03_GeneralLedger AS corr ON r.corr_d_id = corr.document_id
            """
    create_dr = """CREATE VIEW G05_CashTransactions_Reconciled_DR AS
                SELECT
                    r.id AS id,
                    r.d_id AS d_id,
                    r.cash_type AS cash_type,
                    r.entry_type AS entry_type,
                    r.account AS account,
                    r.currency AS currency,
                    r.amount AS amount,
                    r.amount_LC AS amount_LC,
                    corr.id AS corr_id,
                    corr.document_id AS corr_d_id,
                    corr.entry_type AS corr_entry_type,
                    corr.account AS corr_account,
                    r.r_rate * corr.amount AS corr_projected_amount,
                    r.r_rate * corr.amount_LC AS corr_projected_amount_LC
                    
                    
            FROM G04_CashTransactions_Reconciliations_DR AS r
            LEFT JOIN D03_GeneralLedger AS corr ON r.corr_d_id = corr.document_id
                """

    connection.execute(text(drop_cr))
    connection.execute(text(drop_dr))
    connection.execute(text(create_cr))
    connection.execute(text(create_dr))

def view_cash_union(connection):
    logger.info("Updating view G06_CashTransactions_Union")
    drop = "DROP VIEW IF EXISTS G06_CashTransactions_Union"
    create = """CREATE VIEW G06_CashTransactions_Union AS
                SELECT
                            cash.id AS id,
                            cash.d_id AS d_id,
                            cash.cash_type AS cash_type,
                            cash.currency AS currency,
                            cash.entry_type AS entry_type,
                            cash.account AS account,
                            cash.amount AS amount,
                            cash.amount_LC AS amount_LC
                FROM G02_Cash_GeneralLedger as cash
                UNION ALL
                SELECT
                        corr_dr.corr_id AS id,
                        corr_dr.d_id AS d_id,
                        corr_dr.cash_type AS cash_type,
                        corr_dr.currency AS currency,
                        corr_dr.corr_entry_type AS entry_type,
                        corr_dr.corr_account AS account,
                        corr_dr.corr_projected_amount AS amount,
                        corr_dr.corr_projected_amount_LC AS amount_LC
                FROM G05_CashTransactions_Reconciled_DR as corr_dr
                UNION ALL
                SELECT
                        corr_cr.corr_id AS id,
                        corr_cr.d_id AS d_id,
                        corr_cr.cash_type AS cash_type,
                        corr_cr.currency AS currency,
                        corr_cr.corr_entry_type AS entry_type,
                        corr_cr.corr_account AS account,
                        corr_cr.corr_projected_amount AS amount,
                        corr_cr.corr_projected_amount_LC AS amount_LC
                FROM G05_CashTransactions_Reconciled_CR as corr_cr
                """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_aggregated(connection):
    logger.info("Updating view G07_CashTransactions_Aggregated")
    drop = "DROP VIEW IF EXISTS G07_CashTransactions_Aggregated"
    create = """CREATE VIEW G07_CashTransactions_Aggregated AS
                SELECT
                            d_id,
                            cash_type,
                            currency,
                            IIF(SUM(IIF(entry_type="DR",1,-1)*amount)>0,"DR","CR") AS entry_type,
                            account,
                            ROUND(ABS(SUM(IIF(entry_type="DR",1,-1)*amount)),2) AS amount,
                            ROUND(ABS(SUM(IIF(entry_type="DR",1,-1)*amount_LC)),2) AS amount_LC
                FROM G06_CashTransactions_Union
                GROUP BY d_id, cash_type, currency, account
                """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cashflow_actual(connection):
    logger.info("Updating view G08_CashFlow_Actual")
    drop = "DROP VIEW IF EXISTS G08_CashFlow_Actual"
    create = """CREATE VIEW G08_CashFlow_Actual AS
                SELECT

                            cash.d_id AS d_id,
                            "Actual" AS cash_status,
                            cash.cash_type AS cash_type,
                            dt.name AS d_type,
                            doc.date AS date,
                            doc.number AS number,
                            doc.partner_id AS partner_id,
                            p.name AS partner_name,
                            doc.description AS description,
                            cash.currency AS currency,
                            cash.entry_type AS entry_type,
                            cash.account AS account,
                            a.type_id AS account_type,
                            cash.amount AS amount,
                            cash.amount_LC AS amount_LC
                            
                FROM G07_CashTransactions_Aggregated AS cash
                LEFT JOIN D01_Documents AS doc
                ON cash.d_id = doc.id
                LEFT JOIN D02_DocTypes AS dt
                ON doc.type_id = dt.id
                LEFT JOIN B04_Partners AS p
                ON doc.partner_id = p.id
                LEFT JOIN B02_Accounts AS a
                ON cash.account = a.code
                WHERE cash.amount <> 0
                ORDER BY doc.date, cash.d_id
                """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_cashflow_actual_corresponding(connection):
    logger.info("Updating view G09_CashFlow_Actual_Corresponding")
    drop = "DROP VIEW IF EXISTS G09_CashFlow_Actual_Corresponding"
    create = """CREATE VIEW G09_CashFlow_Actual_Corresponding AS
                SELECT 
                        cf.* 
                FROM G08_CashFlow_Actual AS cf
                LEFT JOIN B02_Accounts AS a ON cf.account = a.code
                WHERE a.type_id <> 1 or a.type_id IS NULL
                ORDER BY cf.date, cf.d_id
                """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_documents_pending(connection):
    logger.info("Updating view H01_Documents_Pending")
    drop = "DROP VIEW IF EXISTS H01_Documents_Pending"
    create = """CREATE VIEW H01_Documents_Pending AS
                SELECT 
                    gl.id AS id,
                    d.id AS d_id,
                    "Pending" AS cash_status,
                    IIF(a.type_id = 2, "Receipt", "Payment") AS cash_type,
                    dt.name AS d_type,
                    d.number AS number,
                    gl.date AS date,
                    gl.date_due AS date_due,
                    IIF(gl.date_planned_clearing IS NULL, IIF(gl.date_due IS NULL OR gl.date_due < DATE(), DATE(), gl.date_due), IIF(gl.date_planned_clearing < DATE(), DATE(), gl.date_planned_clearing)) AS p_date,
                    d.description AS description,
                    gl.partner_id AS partner_id,
                    p.name AS partner_name,
                    gl.entry_type AS gl_entry_type,
                    gl.account AS gl_account,
                    a.type_id AS gl_account_type,
                    gl.currency AS currency,
                    IIF(a.type_id = 2, 1, -1) * IIF(gl.entry_type = "DR", 1, -1) * gl.amount AS amount,
                    IIF(a.type_id = 2, 1, -1) * IIF(gl.entry_type = "DR", 1, -1) * gl.amount_LC AS amount_LC,
                    IIF(a.type_id = 2, 1, -1) * IIF(gl.entry_type = "DR", 1, -1) * gl.cleared_amount AS cleared_amount,
                    IIF(a.type_id = 2, 1, -1) * IIF(gl.entry_type = "DR", 1, -1) * (gl.amount_LC / gl.amount) * gl.cleared_amount AS cleared_amount_LC,
                    IIF(a.type_id = 2, 1, -1) * IIF(gl.entry_type = "DR", 1, -1) * (gl.amount - gl.cleared_amount) AS remaining_amount,
                    IIF(a.type_id = 2, 1, -1) * IIF(gl.entry_type = "DR", 1, -1) * (gl.amount_LC / gl.amount ) * (gl.amount - gl.cleared_amount) AS remaining_amount_LC,
                    ((gl.amount - gl.cleared_amount) / gl.amount) AS r_rate,
                    gl.cleared AS cleared,
                    gl.date_cleared AS date_cleared,
                    gl.memo AS memo,
                    gl.priority AS priority,
                    gl.void AS void 
                FROM G00_GeneralLedger AS gl
                JOIN B02_Accounts AS a 
                    ON gl.account = a.code
                JOIN D01_Documents AS d
                    ON gl.document_id = d.id
                LEFT JOIN D02_DocTypes AS dt
                    ON d.type_id = dt.id
                LEFT JOIN B04_Partners AS p
                    ON gl.partner_id = p.id
                LEFT JOIN G01_CashTransactions AS cash
                    ON gl.document_id = cash.d_id
                WHERE cash.id IS NULL AND a.type_id IN (2, 3) AND gl.amount <> 0
                """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_casflow_pending_corresponding(connection):
    logger.info("Updating view H02_CashFlow_Pending_Corresponding")
    drop = "DROP VIEW IF EXISTS H02_CashFlow_Pending_Corresponding"
    create = """CREATE VIEW H02_CashFlow_Pending_Corresponding AS
                SELECT 
                    cf.d_id,
                    cf.cash_status,
                    cf.cash_type,
                    cf.d_type,
                    cf.number,
                    cf.date,
                    cf.p_date,
                    cf.description,
                    cf.partner_id,
                    cf.partner_name,
                    gl.currency,
                    gl.entry_type,
                    gl.account,
                    gl.amount * cf.r_rate AS p_amount,
                    gl.amount_LC * cf.r_rate AS p_amount_LC
                FROM H01_Documents_Pending AS cf
                LEFT JOIN G00_GeneralLedger AS gl 
                    ON cf.d_id = gl.document_id
                WHERE gl.account <> cf.gl_account AND (cf.void = 0 OR cf.void IS NULL) AND cf.cleared = 0
                ORDER BY cf.p_date, cf.d_id
                """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_reconciliations(connection):
    logger.info("Updating view H03_Reconciliations_CR")
    logger.info("Updating view H04_Reconciliations_DR")

    drop_cr = "DROP VIEW IF EXISTS H03_Reconciliations_CR"
    drop_dr = "DROP VIEW IF EXISTS H04_Reconciliations_DR"

    create_cr = """CREATE VIEW H03_Reconciliations_CR AS
                SELECT 
                    r.id,
                    r.dr_docid,
                    r.cr_docid,
                    doc.type_id AS type_id,    
                    t.name AS type_name,
                    doc.number AS number,
                    cr.date AS date,
                    doc.description AS description,
                    cr.partner_id AS partner_id,
                    p.name AS partner_name,
                    r.amount AS r_amount,
                    r.currency AS currency,
                    cr.amount AS cr_amount
                        
                FROM D04_Reconciliations AS r 
                LEFT JOIN D03_GeneralLedger AS cr 
                    ON r.cr_docid = cr.document_id AND r.currency = cr.currency AND r.account = cr.account
                LEFT JOIN D01_Documents AS doc
                    ON cr.document_id = doc.id
                LEFT JOIN D02_DocTypes AS t 
                    ON doc.type_id = t.id
                LEFT JOIN B04_Partners AS p 
                    ON cr.partner_id = p.id
                
                    
                ORDER BY cr.date DESC, cr.id DESC
                """
    create_dr = """CREATE VIEW H04_Reconciliations_DR AS
                    SELECT 
                        r.id,
                        r.dr_docid,
                        r.cr_docid,
                        doc.type_id AS type_id,    
                        t.name AS type_name,
                        doc.number AS number,
                        dr.date AS date,
                        doc.description AS description,
                        dr.partner_id AS partner_id,
                        p.name AS partner_name,
                        r.amount AS r_amount,
                        r.currency AS currency,
                        dr.amount AS dr_amount

                    FROM D04_Reconciliations AS r 
                    LEFT JOIN D03_GeneralLedger AS dr 
                        ON r.dr_docid = dr.document_id AND r.currency = dr.currency AND r.account = dr.account
                    LEFT JOIN D01_Documents AS doc
                        ON dr.document_id = doc.id
                    LEFT JOIN D02_DocTypes AS t 
                        ON doc.type_id = t.id
                    LEFT JOIN B04_Partners AS p 
                        ON dr.partner_id = p.id


                    ORDER BY dr.date DESC, dr.id DESC
                    """


    connection.execute(text(drop_cr))
    connection.execute(text(drop_dr))
    connection.execute(text(create_cr))
    connection.execute(text(create_dr))



def view_import_documents(connection):
    logger.info("Updating view I01_Import_FinancialDoc")
    drop = "DROP VIEW IF EXISTS I01_Import_FinancialDoc"
    create = """CREATE VIEW I01_Import_FinancialDoc AS
                SELECT 
                    FinancialDocID AS id,
                    FinancialDocNo AS number,
                    DocumentTypeID AS type_id,
                    FinancialDocDate AS date,
                    DisbursementTerm AS date_due,
                    CurrencyCode AS currency,
                    DocAmount AS amount,
                    ROUND(DocAmount * Rate,2) AS amount_LC,
                    PartnerID AS partner_id,
                    Comments AS description

                FROM Jumis_FinancialDoc AS doc LEFT JOIN Jumis_Currency AS c 
                ON doc.DocCurrencyID = c.CurrencyID
                LEFT JOIN Jumis_CurrencyRates AS r 
                ON doc.FinancialDocDate = r.RateDate AND doc.DocCurrencyID = r.CurrencyID
                """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_import_gl(connection):
    logger.info("Updating view I02_Import_FinancialDocLine")
    drop = "DROP VIEW IF EXISTS I02_Import_FinancialDocLine"
    create = """CREATE VIEW I02_Import_FinancialDocLine AS
                WITH gl AS 
                    ( 
                    SELECT
                         l.FinancialDocLineID * 10 AS id,
                        l.FinancialDocID AS document_id,
                         l.LineDate AS date,
                         d.DisbursementTerm AS date_due,
                         d.PartnerID AS partner_id,
                         "CR" AS entry_type,
                         cr.AccountCode AS account,
                         c.CurrencyCode AS currency,
                         l.Amount AS amount,
                         ROUND(l.Amount * r.Rate, 2) AS amount_LC
                    FROM Jumis_FinancialDocLine AS l 
                    JOIN Jumis_FinancialDoc AS d 
                        ON l.FinancialDocID = d.FinancialDocID
                    JOIN Jumis_Account AS cr 
                        ON l.CreditID = cr.AccountID
                    JOIN Jumis_Currency AS c
                        ON l.CurrencyID = c.CurrencyID
                    JOIN Jumis_CurrencyRates AS r 
                        ON r.CurrencyID = l.CurrencyID AND r.RateDate = l.LineDate 

                    UNION

                    SELECT
                         l.FinancialDocLineID * 10 + 1 AS id,
                        l.FinancialDocID AS document_id,
                         l.LineDate AS date,
                         d.DisbursementTerm AS date_due,
                         d.PartnerID AS partner_id,
                         "DR" AS entry_type,
                         dr.AccountCode AS account,
                         c.CurrencyCode AS currency,
                         l.Amount AS amount,
                         ROUND(l.Amount * r.Rate, 2) AS amount_LC
                    FROM Jumis_FinancialDocLine AS l 
                    JOIN Jumis_FinancialDoc AS d 
                        ON l.FinancialDocID = d.FinancialDocID
                    JOIN Jumis_Account AS dr 
                        ON l.DebetID = dr.AccountID
                    JOIN Jumis_Currency AS c
                        ON l.CurrencyID = c.CurrencyID
                    JOIN Jumis_CurrencyRates AS r 
                        ON r.CurrencyID = l.CurrencyID AND r.RateDate = l.LineDate 
                    )


                    SELECT 
                        document_id,
                        date,
                        date_due,
                        partner_id,
                        IIF(SUM(amount * IIF(entry_type = "DR",1,-1)) > 0,"DR","CR") AS entry_type,
                        account,
                        currency,
                        ABS(SUM(amount * IIF(entry_type = "DR", 1, -1))) AS amount,
                        ABS(SUM(amount_LC * IIF(entry_type = "DR", 1, -1))) AS amount_LC
                    FROM gl
                    GROUP BY
                        document_id,
                        date,
                        date_due,
                        partner_id,
                        account,
                        currency
                """

    connection.execute(text(drop))
    connection.execute(text(create))

if __name__ == "__main__":
    engine = create_engine_db()

    with engine.connect() as connection:
        views_all(connection)
        connection.commit()