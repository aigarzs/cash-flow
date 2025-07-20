import pandas as pd
from sqlalchemy import text

from cash_flow.database.AEngine import engine_jumis, engine_db

def sync_accounts():
    # ################################################
    # Import all accounts from Jumis no Genie
    # ################################################

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

if __name__ == "__main__":
    sync_accounts()