from sqlalchemy import text
from cash_flow.database.AEngine import engine



def views_all(connection):
    view_general_ledger(connection)
    view_cash_transactions(connection)
    view_cash_generalledger(connection)
    view_cash_corresponding(connection)
    view_cash_reconciliations(connection)
    view_cash_reconciled(connection)
    view_cash_union(connection)
    view_cash_aggregated(connection)
    view_cashflow(connection)


def view_general_ledger(connection):
    drop = "DROP VIEW IF EXISTS G01_GeneralLedger"
    create = """CREATE VIEW G01_GeneralLedger AS
    SELECT 
                            min(gl.id) AS id,
                            d.id AS d_id, 
                            d.date AS d_date,
                            d.currency AS d_currency,
                            IIF(SUM(IIF(gl.entry_type == "DR", 1, -1) * gl.amount)> 0, "DR", "CR") AS gl_entry_type,
                            gl.account AS gl_account,
                            ABS(SUM(IIF(gl.entry_type == "DR", 1, -1) * gl.amount)) AS gl_amount,
                            ABS(SUM(IIF(gl.entry_type == "DR", 1, -1) * gl.amount_LC)) AS gl_amount_LC
                                                        
                        FROM D03_GeneralLedger AS gl 
                        LEFT JOIN D01_Documents AS d ON gl.document_id = d.id
                        GROUP BY d.id, d.currency, gl.account    
    """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_transactions(connection):
    drop = "DROP VIEW IF EXISTS G02_CashTransactions"
    create = """CREATE VIEW G02_CashTransactions AS
        SELECT 
                                gl.id AS id,
                            gl.d_id AS d_id, 
                            d.date AS d_date,
                            IIF(gl.gl_entry_type = "DR", "Receipt", "Payment") AS cash_type,
                            gl.d_currency AS d_currency,
                            gl.gl_entry_type AS gl_entry_type,
                            gl.gl_account AS gl_account,
                            gl.gl_amount  AS gl_amount,
                            gl.gl_amount_LC AS gl_amount_LC
                                                        
                        FROM B03_AccountTypes AS t
                        LEFT JOIN B02_Accounts AS a ON t.id = a.type_id
                        LEFT JOIN G01_GeneralLedger AS gl ON a.code = gl.gl_account
                        LEFT JOIN D01_Documents AS d ON gl.d_id = d.id                        
                        WHERE t.id = 1 AND gl.id IS NOT NULL
                        ORDER BY d.date, gl.d_id
        """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_generalledger(connection):
    drop = "DROP VIEW IF EXISTS G03_Cash_GeneralLedger"
    create = """CREATE VIEW G03_Cash_GeneralLedger AS
            SELECT 
                            gl.id AS id,
                            gl.d_id AS d_id,
                            cash.cash_type AS cash_type,
                            doc.type_id AS d_type,
                            doc.date AS d_date,
                            doc.number AS d_number,
                            doc.customer_id AS d_customer_id,
                            doc.vendor_id AS d_vendor_id,
                            doc.description AS d_description, 
                            gl.d_currency AS d_currency,
                            gl.gl_entry_type AS gl_entry_type,
                            gl.gl_account AS gl_account,
                            gl.gl_amount AS gl_amount,
                            gl.gl_amount_LC AS gl_amount_LC
                             
            FROM G02_CashTransactions AS cash 
            LEFT JOIN G01_GeneralLedger AS gl
            ON cash.d_id = gl.d_id
            LEFT JOIN D01_Documents AS doc
            ON gl.d_id = doc.id
            """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_corresponding(connection):
    drop = "DROP VIEW IF EXISTS G04_CashTransactions_Corresponding"
    create = """CREATE VIEW G04_CashTransactions_Corresponding AS
            SELECT 
                    gl.id AS id,
                    cash.d_id AS d_id, 
                    cash.d_currency AS d_currency,
                    cash.cash_type AS cash_type,
                    gl.gl_entry_type AS gl_entry_type,
                    gl.gl_account AS gl_account,
                    a.type_id AS gl_account_type,
                    gl.gl_amount AS gl_amount,
                    gl.gl_amount_LC AS gl_amount_LC 
                FROM G02_CashTransactions AS cash 
                LEFT JOIN G01_GeneralLedger AS gl 
                ON cash.d_id = gl.d_id AND cash.id <> gl.id
                LEFT JOIN B02_Accounts AS a ON gl.gl_account = a.code
            """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_reconciliations(connection):
    drop = "DROP VIEW IF EXISTS G05_CashTransactions_Reconciliations"
    create = """CREATE VIEW G05_CashTransactions_Reconciliations AS
            SELECT 
                    cash.id AS cash_id,
                    cash.d_id AS cash_d_id, 
                    cash.d_currency AS cash_currency,
                    cash.cash_type AS cash_type,
                    cash.gl_entry_type AS cash_gl_entry_type,
                    cash.gl_account AS gl_account,
                    cash.gl_account_type AS gl_account_type,
                    cash.gl_amount AS cash_gl_amount,
                    cash.gl_amount_LC AS cash_gl_amount_LC,
                    r.id AS r_id,
                    r.amount AS r_amount,
                    r.invoice_id AS invoice_d_id,
                    invoice.gl_entry_type AS invoice_gl_entry_type,
                    invoice.gl_amount AS invoice_gl_amount,
                    invoice.gl_amount_LC AS invoice_gl_amount_LC,
                    IIF(invoice.gl_amount <> 0, r.amount / invoice.gl_amount, 0) AS r_rate
                
                FROM G04_CashTransactions_Corresponding AS cash
                LEFT JOIN D04_Reconciliations AS r
                ON cash.gl_account_type IN (2,3) AND cash.d_id = r.payment_id AND cash.d_currency = r.currency
                LEFT JOIN G01_GeneralLedger AS invoice ON invoice.d_id = r.invoice_id AND cash.gl_account = invoice.gl_account AND cash.d_currency = invoice.d_currency AND cash.gl_entry_type <> invoice.gl_entry_type
                WHERE r.id IS NOT NULL
            """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_reconciled(connection):
    drop = "DROP VIEW IF EXISTS G06_CashTransactions_Reconciled"
    create = """CREATE VIEW G06_CashTransactions_Reconciled AS
            SELECT
                    r.cash_id AS cash_id,
                    r.cash_d_id AS cash_d_id,
                    r.cash_gl_entry_type AS cash_gl_entry_type,
                    r.gl_account AS cash_gl_account,
                    r.cash_gl_amount AS cash_gl_amount,
                    r.cash_gl_amount_LC AS cash_gl_amount_LC,
                    invoice.id AS invoice_id,
                    invoice.d_id AS invoice_d_id,
                    invoice.d_currency AS d_currency,
                    invoice.gl_entry_type AS invoice_gl_entry_type,
                    invoice.gl_account AS invoice_gl_account,
                    r.r_rate * invoice.gl_amount AS invoice_projected_amount,
                    r.r_rate * invoice.gl_amount_LC AS invoice_projected_amount_LC
                    
                    
            FROM G05_CashTransactions_Reconciliations AS r
            LEFT JOIN G01_GeneralLedger AS invoice ON r.invoice_d_id = invoice.d_id
            """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_union(connection):
    drop = "DROP VIEW IF EXISTS G07_CashTransactions_Union"
    create = """CREATE VIEW G07_CashTransactions_Union AS
                SELECT
                            cash.id AS id,
                            cash.d_id AS d_id,
                            cash.d_currency AS d_currency,
                            cash.gl_entry_type AS gl_entry_type,
                            cash.gl_account AS gl_account,
                            cash.gl_amount AS gl_amount,
                            cash.gl_amount_LC AS gl_amount_LC
                FROM G03_Cash_GeneralLedger as cash
                UNION ALL
                SELECT
                        cor.invoice_id AS id,
                        cor.cash_d_id AS d_id,
                        cor.d_currency AS d_currency,
                        cor.invoice_gl_entry_type AS gl_entry_type,
                        cor.invoice_gl_account AS gl_account,
                        cor.invoice_projected_amount AS gl_amount,
                        cor.invoice_projected_amount_LC AS gl_amount_LC
                FROM G06_CashTransactions_Reconciled as cor
                """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_aggregated(connection):
    drop = "DROP VIEW IF EXISTS G08_CashTransactions_Aggregated"
    create = """CREATE VIEW G08_CashTransactions_Aggregated AS
                SELECT
                            d_id,
                            d_currency,
                            IIF(SUM(IIF(gl_entry_type="DR",1,-1)*gl_amount)>0,"DR","CR") AS gl_entry_type,
                            gl_account,
                            ROUND(ABS(SUM(IIF(gl_entry_type="DR",1,-1)*gl_amount)),2) AS gl_amount,
                            ROUND(ABS(SUM(IIF(gl_entry_type="DR",1,-1)*gl_amount_LC)),2) AS gl_amount_LC
                FROM G07_CashTransactions_Union
                GROUP BY d_id, d_currency, gl_account
                """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cashflow(connection):
    drop = "DROP VIEW IF EXISTS G09_CashFlow"
    create = """CREATE VIEW G09_CashFlow AS
                SELECT

                            cash.d_id AS d_id,
                            doc.type_id AS d_type,
                            doc.date AS d_date,
                            doc.number AS d_number,
                            doc.customer_id AS d_customer_id,
                            doc.vendor_id AS d_vendor_ir,
                            doc.description AS d_description,
                            cash.d_currency AS d_currency,
                            cash.gl_entry_type AS gl_entry_type,
                            cash.gl_account AS gl_account,
                            cash.gl_amount AS gl_amount,
                            cash.gl_amount_LC AS gl_amount_LC
                            
                FROM G08_CashTransactions_Aggregated AS cash
                LEFT JOIN D01_Documents AS doc
                ON cash.d_id = doc.id
                WHERE cash.gl_amount <> 0
                ORDER BY doc.date, cash.d_id
                """

    connection.execute(text(drop))
    connection.execute(text(create))


if __name__ == "__main__":
    with engine.connect() as connection:
        views_all(connection)
        connection.commit()