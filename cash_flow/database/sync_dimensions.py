import numpy as np
import pandas as pd
from sqlalchemy import text

from cash_flow.database.AEngine import create_engine_jumis, create_engine_db
from cash_flow.database.Model import Source


def sync_accounts():
    # ################################################
    # Import all accounts from Jumis no Genie
    # ################################################
    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_Account"))
        conn.commit()

    page_size = 100
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                WITH Jumis_Account AS (
                    SELECT AccountID, AccountCode, AccountName, CreateDate, UpdateDate,
                    ROW_NUMBER() OVER (ORDER BY AccountID) AS rn
                    FROM dbo.Account
                    WHERE AccountPlanIsBussiness = 1 
                    AND AccountCode IS NOT NULL 
                    AND AccountCode <> '...' 
                    )
                SELECT * FROM Jumis_Account
                WHERE rn BETWEEN :lower AND :upper
            """)


        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                            )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_Account", engine_db, if_exists="append", index=False)
            page += 1

    # ################################################
    # Syncing Jumis_Account with B02_Accounts
    # ################################################

    # Load source and target tables into DataFrames
    df_source = pd.read_sql("SELECT * FROM Jumis_Account", engine_db)
    df_target = pd.read_sql("SELECT * FROM B02_Accounts", engine_db)

    # Merge on Code to compare existing records
    df_merged = df_source.merge(df_target, how='outer', left_on='AccountCode', right_on='code',
                                indicator=True,
                                suffixes=('_src', '_tgt'))

    # Identify new records (present in source, not in target)
    df_new = df_merged[df_merged['_merge'] == 'left_only'][['AccountCode', 'AccountName']]

    # Identify deleted records (present in target, not in source)
    df_deleted = df_merged[df_merged['_merge'] == 'right_only'][['code']]

    # Identify potential updates
    df_common = df_merged[df_merged['_merge'] == 'both']
    df_updates = df_common[
        (df_common['AccountName'] != df_common['name'])
    ][['AccountCode', 'AccountName']]

    with engine_db.begin() as conn:
        # Delete records
        for row in df_deleted.itertuples():
            conn.execute(text("DELETE FROM B02_Accounts WHERE code = :code"), {'code': row.code})

        # Insert new records
        for row in df_new.itertuples():
            conn.execute(text("""
                              INSERT INTO B02_Accounts (code, name)
                              VALUES (:code, :name)
                              """), {
                             'code': row.AccountCode,
                             'name': row.AccountName
                         })

        # Update changed records
        for row in df_updates.itertuples():
            conn.execute(text("""
                              UPDATE B02_Accounts
                              SET name = :name
                              WHERE code = :code
                              """), {
                             'code': row.AccountCode,
                             'name': row.AccountName
                         })

        # conn.commit()

def sync_currencies():
    # ################################################
    # Import all currencies from Jumis no Genie
    # ################################################
    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_Currency"))
        conn.commit()

    page_size = 100
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                WITH Jumis_Currency AS (
                    SELECT CurrencyID, CurrencyCode, Description,
                    ROW_NUMBER() OVER (ORDER BY CurrencyID) AS rn
                    FROM dbo.Currency
                    WHERE CurrencyCode IS NOT NULL 
                    )
                SELECT * FROM Jumis_Currency
                WHERE rn BETWEEN :lower AND :upper
            """)


        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                            )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_Currency", engine_db, if_exists="append", index=False)
            page += 1

    # ################################################
    # Syncing Jumis_Currency with B01_Currencies
    # ################################################

    # Load source and target tables into DataFrames
    df_source = pd.read_sql("SELECT * FROM Jumis_Currency", engine_db)
    df_target = pd.read_sql("SELECT * FROM B01_Currencies", engine_db)

    # Merge on Code to compare existing records
    df_merged = df_source.merge(df_target, how='outer', left_on='CurrencyCode', right_on='code',
                                indicator=True,
                                suffixes=('_src', '_tgt'))

    # Identify new records (present in source, not in target)
    df_new = df_merged[df_merged['_merge'] == 'left_only'][['CurrencyCode', 'Description']]

    # Identify deleted records (present in target, not in source)
    df_deleted = df_merged[df_merged['_merge'] == 'right_only'][['code']]

    # Identify potential updates
    df_common = df_merged[df_merged['_merge'] == 'both']
    df_updates = df_common[
        (df_common['Description'] != df_common['name'])
    ][['CurrencyCode', 'Description']]

    with engine_db.begin() as conn:
        # Delete records
        for row in df_deleted.itertuples():
            conn.execute(text("DELETE FROM B01_Currencies WHERE code = :code"), {'code': row.code})

        # Insert new records
        for row in df_new.itertuples():
            conn.execute(text("""
                              INSERT INTO B01_Currencies (code, name)
                              VALUES (:code, :name)
                              """), {
                             'code': row.CurrencyCode,
                             'name': row.Description
                         })

        # Update changed records
        for row in df_updates.itertuples():
            conn.execute(text("""
                              UPDATE B01_Currencies
                              SET name = :name
                              WHERE code = :code
                              """), {
                             'code': row.CurrencyCode,
                             'name': row.Description
                         })

        # conn.commit()

def sync_partners():
    # ################################################
    # Import all partners from Jumis no Genie
    # ################################################
    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_Partner"))
        conn.commit()

    page_size = 1000
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                WITH Jumis_Partner AS (
                    SELECT PartnerID, PartnerName, PhysicalPersonFirstName, CreateDate, UpdateDate,
                    ROW_NUMBER() OVER (ORDER BY PartnerID) AS rn
                    FROM dbo.Partner
                    )
                SELECT * FROM Jumis_Partner
                WHERE rn BETWEEN :lower AND :upper
            """)


        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                            )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_Partner", engine_db, if_exists="append", index=False)
            page += 1

    # ################################################
    # Syncing Jumis_Partner with B04_Partners
    # ################################################

    # Load source and target tables into DataFrames
    df_source = pd.read_sql("SELECT * FROM Jumis_Partner", engine_db)
    df_target = pd.read_sql("SELECT * FROM B04_Partners", engine_db)

    # Merge on Code to compare existing records
    df_merged = df_source.merge(df_target, how='outer', left_on='PartnerID', right_on='id',
                                indicator=True,
                                suffixes=('_src', '_tgt'))

    # Identify new records (present in source, not in target)
    df_new = df_merged[df_merged['_merge'] == 'left_only'][['PartnerID', 'PartnerName', 'PhysicalPersonFirstName', 'CreateDate', 'UpdateDate']]
    df_new['PhysicalPersonFirstName'] = df_new['PhysicalPersonFirstName'].fillna('').str.strip()
    df_new['PartnerName'] = np.where(
        df_new['PhysicalPersonFirstName'] == '',
        df_new['PartnerName'],
        (df_new['PartnerName'] + ' ' + df_new['PhysicalPersonFirstName']).str.strip()
    )

    # Identify deleted records (present in target, not in source)
    df_deleted = df_merged[df_merged['_merge'] == 'right_only'][['id']]

    # Identify potential updates
    df_common = df_merged[df_merged['_merge'] == 'both']
    # Fill NaNs with empty strings first
    df_common['PhysicalPersonFirstName'] = df_common['PhysicalPersonFirstName'].fillna('').str.strip()
    df_common['PartnerName'] = np.where(
        df_common['PhysicalPersonFirstName'] == '',
        df_common['PartnerName'],
        (df_common['PartnerName'] + ' ' + df_common['PhysicalPersonFirstName']).str.strip()
    )

    df_updates = df_common[
        (df_common['PartnerName'] != df_common['name'])
    ][['PartnerID', 'PartnerName']]

    with engine_db.begin() as conn:
        # Delete records
        for row in df_deleted.itertuples():
            conn.execute(text("DELETE FROM B04_Partners WHERE id = :id"), {'id': row.id})

        # Insert new records
        for row in df_new.itertuples():
            conn.execute(text("""
                              INSERT INTO B04_Partners (id, name, cr_priority, dr_priority, cr_void, dr_void)
                              VALUES (:id, :name, 100, 100, 0, 0)
                              """), {
                             'name': row.PartnerName,
                             'id': row.PartnerID
                         })

        # Update changed records
        for row in df_updates.itertuples():
            conn.execute(text("""
                              UPDATE B04_Partners
                              SET name = :name
                              WHERE 
                              id = :id 
                              """), {
                             'name': row.PartnerName,
                             'id': row.PartnerID
                         })

        # conn.commit()

def sync_doctypes():
    # ################################################
    # Import all doctypes from Jumis no Genie
    # ################################################
    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_DocumentType"))
        conn.commit()

    page_size = 100
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                WITH Jumis_DocumentType AS (
                    SELECT DocumentTypeID, TypeName, TypeShortName,
                    ROW_NUMBER() OVER (ORDER BY DocumentTypeID) AS rn
                    FROM dbo.DocumentType
                    )
                SELECT * FROM Jumis_DocumentType
                WHERE rn BETWEEN :lower AND :upper
            """)


        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                            )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_DocumentType", engine_db, if_exists="append", index=False)
            page += 1

    # ################################################
    # Syncing Jumis_DocumentType with D02_DocTypes
    # ################################################
    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM D02_DocTypes"))
        conn.commit()
        conn.execute(text("""
                            INSERT INTO D02_DocTypes (id, name) 
                            SELECT DocumentTypeID, TypeShortName 
                            FROM Jumis_DocumentType
                        """))
        conn.commit()


def sync_currencyrates():
    # ################################################
    # Import all currency rates from Jumis no Genie
    # ################################################
    engine_db = create_engine_db()
    engine_jumis = create_engine_jumis()

    with engine_db.connect() as conn:
        conn.execute(text("DELETE FROM Jumis_CurrencyRates"))
        conn.commit()

    page_size = 100
    page = 1
    has_more = True

    while has_more:
        lower_bound = (page - 1) * page_size + 1
        upper_bound = page * page_size

        query = text(
            f"""
                WITH Jumis_CurrencyRates AS (
                    SELECT RateID, CurrencyID, RateDate, Rate,
                    ROW_NUMBER() OVER (ORDER BY RateID) AS rn
                    FROM dbo.CurrencyRates
                    )
                SELECT * FROM Jumis_CurrencyRates
                WHERE rn BETWEEN :lower AND :upper
            """)


        with engine_jumis.connect() as conn:
            df = pd.read_sql(query, con=conn,
                             params={"lower": lower_bound, "upper": upper_bound}
                            )

        if df.empty:
            has_more = False
        else:
            df.to_sql("Jumis_CurrencyRates", engine_db, if_exists="append", index=False)
            page += 1




if __name__ == "__main__":
    sync_accounts()
    sync_currencies()
    sync_currencyrates()
    sync_partners()
    sync_doctypes()