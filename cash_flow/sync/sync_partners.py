import pandas as pd
from sqlalchemy import text

from cash_flow.database.AEngine import engine_jumis, engine_db

def sync_partners():
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
                    SELECT PartnerID, PartnerName, CreateDate, UpdateDate,
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



if __name__ == "__main__":
    sync_partners()