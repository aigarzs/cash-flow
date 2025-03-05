from sqlalchemy import text
from cash_flow.database.AEngine import engine



def views_all(connection):
    view_bank_receipts_reconciled(connection)
    view_bank_receipts(connection)
    view_bank_receipts_union(connection)
    view_bank_receipts_agg(connection)
    view_bank_payments_reconciled(connection)
    view_bank_payments(connection)
    view_bank_payments_union(connection)
    view_bank_payments_agg(connection)
    view_bank_union(connection)
    view_cash_transactions(connection)
    view_bank_payments_planned(connection)
    view_bank_receipts_planned(connection)





def view_bank_receipts_reconciled(connection):
    drop = "DROP VIEW IF EXISTS D11_CF_BankReceipts_Reconciled"
    create = """CREATE VIEW D11_CF_BankReceipts_Reconciled AS
                        SELECT 
                            gl.id AS id,
                            d.id AS d_id, 
                            d.type_id AS d_type, 
                            d.date AS d_date, 
                            d.number AS d_number, 
                            d.customer_id AS d_customer, 
                            d.description AS d_description, 
                            d.amount AS d_amount, 
                            d.currency AS d_currency,
                            d.amount_LC AS d_amount_LC,
                            IIF(d.currency = r.currency, r.amount / d.amount, NULL) AS d_Rate, 
                            r.id AS r_id,
                            r.amount AS r_Amount,
                            r.currency AS r_Currency,
                            c.id AS c_id,
                            c.type_id AS c_type,
                            c.date AS c_date,
                            c.number AS c_number,
                            c.customer_id AS c_customer,
                            c.description AS c_description,
                            c.amount AS c_amount,
                            c.currency AS c_currency,
                            c.amount_LC AS c_amount_LC,
                            IIF(c.currency = r.currency, r.amount / c.amount, NULL) AS c_Rate,
                            gl.id AS gl_id,
                            gl.entry_type AS gl_entry_type,
                            gl.account AS gl_account,
                            gl.amount AS gl_amount,
                            gl.amount_LC AS gl_amount_LC,
                            gl.amount * r.amount / c.amount AS gl_amount_projected,
                            gl.amount_LC * r.amount / c.amount AS gl_amount_LC_projected
                            
                        FROM D01_Documents AS d
                        LEFT JOIN D04_Reconciliations AS r ON r.payment_id = d.id
                        LEFT JOIN D01_Documents AS c ON r.invoice_id = c.id
                        LEFT JOIN D03_GeneralLedger AS gl ON gl.document_id = c_id  

                        WHERE d.type_id = 1 AND r.id IS NOT NULL
                        
                        """


    connection.execute(text(drop))
    connection.execute(text(create))


def view_bank_payments_reconciled(connection):
    drop = "DROP VIEW IF EXISTS D11_CF_BankPayments_Reconciled"
    create = """CREATE VIEW D11_CF_BankPayments_Reconciled AS
                        SELECT d.id AS d_id, 
                            d.type_id AS d_type, 
                            d.date AS d_date, 
                            d.number AS d_number, 
                            d.vendor_id AS d_vendor, 
                            d.description AS d_description, 
                            d.amount AS d_amount, 
                            d.currency AS d_currency,
                            d.amount_LC AS d_amount_LC,
                            IIF(d.currency = r.currency, r.amount / d.amount, NULL) AS d_Rate, 
                            r.id AS r_id,
                            r.amount AS r_Amount,
                            r.currency AS r_Currency,
                            c.id AS c_id,
                            c.type_id AS c_type,
                            c.date AS c_date,
                            c.number AS c_number,
                            c.vendor_id AS c_vendor,
                            c.description AS c_description,
                            c.amount AS c_amount,
                            c.currency AS c_currency,
                            c.amount_LC AS c_amount_LC,
                            IIF(c.currency = r.currency, r.amount / c.amount, NULL) AS c_Rate,
                            gl.id AS gl_id,
                            gl.entry_type AS gl_entry_type,
                            gl.account AS gl_account,
                            gl.amount AS gl_amount,
                            gl.amount_LC AS gl_amount_LC,
                            gl.amount * r.amount / c.amount AS gl_amount_projected,
                            gl.amount_LC * r.amount / c.amount AS gl_amount_LC_projected

                        FROM D01_Documents AS d
                        LEFT JOIN D04_Reconciliations AS r ON r.payment_id = d.id
                        LEFT JOIN D01_Documents AS c ON r.invoice_id = c.id
                        LEFT JOIN D03_GeneralLedger AS gl ON gl.document_id = c_id  

                        WHERE d.type_id = 2 AND r.id IS NOT NULL

                        """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_bank_receipts(connection):
    drop = "DROP VIEW IF EXISTS D11_CF_BankReceipts"
    create = """CREATE VIEW D11_CF_BankReceipts AS
                        SELECT d.id AS d_id, 
                            d.type_id AS d_type, 
                            d.date AS d_date, 
                            d.number AS d_number, 
                            d.customer_id AS d_customer, 
                            d.description AS d_description, 
                            d.amount AS d_amount, 
                            d.currency AS d_currency,
                            d.amount_LC AS d_amount_LC,
                            gl.id AS gl_id,
                            gl.entry_type AS gl_entry_type,
                            gl.account AS gl_account,
                            gl.amount AS gl_amount,
                            gl.amount_LC AS gl_amount_LC
                            

                        FROM D01_Documents AS d
                        LEFT JOIN D03_GeneralLedger AS gl ON gl.document_id = d.id  

                        WHERE d.type_id = 1 

                        """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_bank_payments(connection):
    drop = "DROP VIEW IF EXISTS D11_CF_BankPayments"
    create = """CREATE VIEW D11_CF_BankPayments AS
                        SELECT d.id AS d_id, 
                            d.type_id AS d_type, 
                            d.date AS d_date, 
                            d.number AS d_number, 
                            d.vendor_id AS d_vendor, 
                            d.description AS d_description, 
                            d.amount AS d_amount, 
                            d.currency AS d_currency,
                            d.amount_LC AS d_amount_LC,
                            gl.id AS gl_id,
                            gl.entry_type AS gl_entry_type,
                            gl.account AS gl_account,
                            gl.amount AS gl_amount,
                            gl.amount_LC AS gl_amount_LC


                        FROM D01_Documents AS d
                        LEFT JOIN D03_GeneralLedger AS gl ON gl.document_id = d.id  

                        WHERE d.type_id = 2 

                        """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_bank_receipts_union(connection):
    drop = "DROP VIEW IF EXISTS D11_CF_BankReceipts_Union"
    create = """CREATE VIEW D11_CF_BankReceipts_Union AS
                        SELECT 
                            d_id, 
                            d_type, 
                            d_date, 
                            d_number, 
                            d_customer, 
                            gl_id,
                            gl_entry_type,
                            gl_account,
                            gl_amount,
                            d_currency,
                            gl_amount_LC
                        FROM D11_CF_BankReceipts
                        UNION ALL
                        SELECT
                            d_id, 
                            d_type, 
                            d_date, 
                            d_number, 
                            d_customer, 
                            gl_id,
                            gl_entry_type,
                            gl_account,
                            gl_amount_projected,
                            c_currency,
                            gl_amount_LC_projected
                        FROM D11_CF_BankReceipts_Reconciled
                        """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_bank_payments_union(connection):
    drop = "DROP VIEW IF EXISTS D11_CF_BankPayments_Union"
    create = """CREATE VIEW D11_CF_BankPayments_Union AS
                        SELECT 
                            d_id, 
                            d_type, 
                            d_date, 
                            d_number, 
                            d_vendor, 
                            gl_id,
                            gl_entry_type,
                            gl_account,
                            gl_amount,
                            d_currency,
                            gl_amount_LC
                        FROM D11_CF_BankPayments
                        UNION ALL
                        SELECT
                            d_id, 
                            d_type, 
                            d_date, 
                            d_number, 
                            d_vendor, 
                            gl_id,
                            gl_entry_type,
                            gl_account,
                            gl_amount_projected,
                            c_currency,
                            gl_amount_LC_projected
                        FROM D11_CF_BankPayments_Reconciled
                        """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_bank_receipts_agg(connection):
    drop = "DROP VIEW IF EXISTS D12_CF_BankReceipts_Aggregated"
    create = """CREATE VIEW D12_CF_BankReceipts_Aggregated AS
                        SELECT 
                            d_id, 
                            d_type, 
                            d_date, 
                            d_customer, 
                            gl_account,
                            IIF(ROUND(SUM(IIF(gl_entry_type=='DR', 1, -1) * gl_amount),2) < 0, 'CR', 'DR') AS gl_entry_type,
                            ROUND(ABS(SUM(IIF(gl_entry_type=='DR', 1, -1) * gl_amount)),2) AS gl_amount,
                            d_currency,
                            ROUND(ABS(SUM(IIF(gl_entry_type=='DR', 1, -1) * gl_amount_LC)),2) AS gl_amount_LC
                        FROM D11_CF_BankReceipts_Union
                        GROUP BY d_id, d_type, d_date, d_customer, gl_account, d_currency
                        ORDER BY d_date, d_id
                        """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_bank_payments_agg(connection):
    drop = "DROP VIEW IF EXISTS D12_CF_BankPayments_Aggregated"
    create = """CREATE VIEW D12_CF_BankPayments_Aggregated AS
                        SELECT 
                            d_id, 
                            d_type, 
                            d_date, 
                            d_vendor, 
                            gl_account,
                            IIF(ROUND(SUM(IIF(gl_entry_type=='DR', 1, -1) * gl_amount),2) < 0, 'CR', 'DR') AS gl_entry_type,
                            ROUND(ABS(SUM(IIF(gl_entry_type=='DR', 1, -1) * gl_amount)),2) AS gl_amount,
                            d_currency,
                            ROUND(ABS(SUM(IIF(gl_entry_type=='DR', 1, -1) * gl_amount_LC)),2) AS gl_amount_LC
                        FROM D11_CF_BankPayments_Union
                        GROUP BY d_id, d_type, d_date, d_vendor, gl_account, d_currency
                        ORDER BY d_date, d_id
                        """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_bank_union(connection):
    drop = "DROP VIEW IF EXISTS D13_CF_Bank_Union"
    create = """CREATE VIEW D13_CF_Bank_Union AS 
                    SELECT 
                        d_id,
                        d_type,
                        d_date,
                        NULL AS d_customer,
                        d_vendor,
                        gl_account,
                        gl_entry_type,
                        gl_amount,
                        d_currency,
                        gl_amount_LC
                    FROM D12_CF_BankPayments_Aggregated
                    UNION SELECT
                        d_id,
                        d_type,
                        d_date,
                        d_customer,
                        NULL AS d_vendor,
                        gl_account,
                        gl_entry_type,
                        gl_amount,
                        d_currency,
                        gl_amount_LC
                    FROM D12_CF_BankReceipts_Aggregated """

    connection.execute(text(drop))
    connection.execute(text(create))

def view_cash_transactions(connection):
    drop = "DROP VIEW IF EXISTS D10_Cash_Transactions"
    create = """CREATE VIEW D10_Cash_Transactions AS
    SELECT 
                            gl.id AS id,
                            d.id AS d_id, 
                            d.type_id AS d_type, 
                            d.number AS d_number,
                            d.date AS d_date, 
                            d.vendor_id AS d_vendor,
                            d.customer_id AS d_customer,
                            d.description AS d_description,
                            d.currency AS d_currency,
                            gl.entry_type AS gl_entry_type,
                            gl.account AS gl_account,
                            gl.amount AS gl_amount,
                            gl.amount_LC AS gl_amount_LC
                                                        
                        FROM B03_AccountTypes AS t
                        LEFT JOIN B02_Accounts AS a ON t.id = a.type_id
                        LEFT JOIN D03_GeneralLedger AS gl ON a.code = gl.account
                        LEFT JOIN D01_Documents AS d ON gl.document_id = d.id
                        WHERE t.id = 1 AND gl.id IS NOT NULL
                        ORDER BY d.date, d.id
                                                
                    """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_bank_payments_planned(connection):
    drop = "DROP VIEW IF EXISTS D14_CF_BankPayments_Planned"
    create = """CREATE VIEW D14_CF_BankPayments_Planned AS
                        SELECT 
                            d.id AS d_id, 
                            d.type_id AS d_type, 
                            d.number AS d_number,
                            d.date AS d_date, 
                            d.date_due AS d_date_due,
                            IIF(d.date_planned_clearing < DATE(), DATE(), d.date_planned_clearing) AS d_date_planned,
                            d.priority AS d_priority,
                            d.vendor_id AS d_vendor, 
                            d.description AS d_description,
                            (d.amount - d.cleared_amount) / d.amount AS c_Rate,
                            d.amount AS d_amount,
                            d.currency AS d_currency,
                            d.amount_LC AS d_amount_LC,
                            ROUND(d.amount - d.cleared_amount,2) AS d_remaining_amount,
                            ROUND(d.amount_LC * (d.amount - d.cleared_amount) / d.amount,2) AS d_remaining_amount_LC,
                            gl.entry_type AS gl_entry_type,
                            gl.account AS gl_account,
                            gl.amount AS gl_amount,
                            gl.amount_LC AS gl_amount_LC,
                            ROUND(gl.amount * (d.amount - d.cleared_amount) / d.amount,2) AS gl_amount_projected,
                            ROUND(gl.amount_LC * (d.amount - d.cleared_amount) / d.amount,2) AS gl_amount_LC_projected
                            
                        FROM D01_Documents AS d
                        LEFT JOIN D03_GeneralLedger AS gl ON d.id = gl.document_id
                        WHERE d.type_id IN (4, 7) AND d.cleared = FALSE
                        ORDER BY d.date_planned_clearing, d.date, d.id
                                                
                    """

    connection.execute(text(drop))
    connection.execute(text(create))


def view_bank_receipts_planned(connection):
    drop = "DROP VIEW IF EXISTS D14_CF_BankReceipts_Planned"
    create = """CREATE VIEW D14_CF_BankReceipts_Planned AS
                        SELECT 
                            d.id AS d_id, 
                            d.type_id AS d_type, 
                            d.number AS d_number,
                            d.date AS d_date, 
                            d.date_due AS d_date_due,
                            IIF(d.date_planned_clearing < DATE(), DATE(), d.date_planned_clearing) AS d_date_planned,
                            d.priority AS d_priority,
                            d.customer_id AS d_customer, 
                            d.description AS d_description,
                            (d.amount - d.cleared_amount) / d.amount AS c_Rate,
                            d.amount AS d_amount,
                            d.currency AS d_currency,
                            d.amount_LC AS d_amount_LC,
                            ROUND(d.amount - d.cleared_amount,2) AS d_remaining_amount,
                            ROUND(d.amount_LC * (d.amount - d.cleared_amount) / d.amount,2) AS d_remaining_amount_LC,
                            gl.entry_type AS gl_entry_type,
                            gl.account AS gl_account,
                            gl.amount AS gl_amount,
                            gl.amount_LC AS gl_amount_LC,
                            ROUND(gl.amount * (d.amount - d.cleared_amount) / d.amount,2) AS gl_amount_projected,
                            ROUND(gl.amount_LC * (d.amount - d.cleared_amount) / d.amount,2) AS gl_amount_LC_projected

                        FROM D01_Documents AS d
                        LEFT JOIN D03_GeneralLedger AS gl ON d.id = gl.document_id
                        WHERE d.type_id = 3 AND d.cleared = FALSE
                        ORDER BY d.date_planned_clearing, d.date, d.id

                    """

    connection.execute(text(drop))
    connection.execute(text(create))

if __name__ == "__main__":
    with engine.connect() as connection:
        views_all(connection)
        connection.commit()