import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.dialects.mysql import insert

import config


def load_rates(df: pd.DataFrame) -> tuple[int, int]:
    """クレンジング済みの為替レートを raw_rates テーブルへ UPSERT する。

    Args:
        df: transform → quality を通った DataFrame（列: date, base, quote, rate）。

    Returns:
        (新規件数, 更新件数) のタプル。
    """
    # ガード節
    if df.empty:
        return 0, 0

    engine = create_engine(config.DATABASE_URL)

    # raw_ratesテーブルのメタデータを取得
    metadata = MetaData()
    table = Table("raw_rates", metadata, autoload_with=engine)

    # DB格納のため、date列をdatetime64型からdate型に変換。
    # 変換はコピーに対して行い、元データはdatetime64のまま残す(集計時のpandas時系列操作のため)
    df = df.copy()
    df["date"] = df["date"].dt.date
    records = df.to_dict(orient="records")

    # UPSERT文
    stmt = insert(table).values(records)
    stmt = stmt.on_duplicate_key_update(rate=stmt.inserted.rate)

    # トランザクション内で「既存キーの取得 → UPSERT」を実行
    with engine.begin() as conn:
        rows = conn.execute(select(table.c.date, table.c.base, table.c.quote)).all()
        existing_keys = {(r.date, r.base, r.quote) for r in rows}

        conn.execute(stmt)

    # 新規追加件数と更新件数をカウントして返す
    inserted = sum(
        1 for r in records if (r["date"], r["base"], r["quote"]) not in existing_keys
    )
    updated = len(records) - inserted

    return inserted, updated


# 動作確認用
if __name__ == "__main__":
    from src.extract import fetch_latest_rates
    from src.quality import check_quality
    from src.transform import transform

    rates = fetch_latest_rates()
    df = transform(rates)
    clean_df = check_quality(df)
    inserted, updated = load_rates(clean_df)
    print(f"新規 {inserted} 件 / 更新 {updated} 件 を raw_rates に書き込みました")
