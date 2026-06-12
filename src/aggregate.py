import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.dialects.mysql import insert

import config


def read_raw_rates(engine) -> pd.DataFrame:
    """raw_rates テーブルを全件読み込み、集計の入力となる DataFrame を返す。

    Args:
        engine: SQLAlchemy の Engine。

    Returns:
        raw_rates の内容（列: date, base, quote, rate）。
    """
    # raw_rates のメタデータを取得し、集計に使う列だけを SELECT
    metadata = MetaData()
    table = Table("raw_rates", metadata, autoload_with=engine)
    stmt = select(table.c.date, table.c.base, table.c.quote, table.c.rate)
    with engine.connect() as conn:
        rows = conn.execute(stmt).all()
        df = pd.DataFrame(rows, columns=["date", "base", "quote", "rate"])

    # date を datetime64 に変換（後段の時系列計算 diff/rolling を安定させるため）
    df["date"] = pd.to_datetime(df["date"])
    return df


def compute_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """日次レートから前日比・7日移動平均を計算した DataFrame を返す。

    Args:
        df: read_raw_rates の戻り値（列: date, base, quote, rate）。

    Returns:
        agg_rates に対応する列を持つ DataFrame
        （date, base, quote, rate, diff_prev, pct_change, ma_7）。
    """
    # 前日比・移動平均は「同じ通貨ペアの時系列」に対して計算する。
    # 通貨ペアをまたいで計算しないよう、(base, quote, date) でソートし groupby(["base", "quote"]) 単位で処理する。
    df_sorted = df.sort_values(["base", "quote", "date"])

    grouped = df_sorted.groupby(["base", "quote"])["rate"]
    df_sorted["diff_prev"] = grouped.diff()  # 前日比（差）
    df_sorted["pct_change"] = grouped.pct_change() * 100  # 前日比（変化率, %）
    # 7日移動平均。groupby().rolling() は MultiIndex になり行がズレるため transform で元の行に揃える。
    # min_periods 既定=window のため、各ペアの最初の6日は NaN（設計通り）。
    df_sorted["ma_7"] = grouped.transform(lambda s: s.rolling(window=7).mean())

    # agg_rates の列順に揃えて返す
    return df_sorted[
        ["date", "base", "quote", "rate", "diff_prev", "pct_change", "ma_7"]
    ]


def save_aggregates(df: pd.DataFrame) -> tuple[int, int]:
    """集計結果を agg_rates テーブルへ UPSERT する。

    Args:
        df: compute_aggregates の戻り値
            （列: date, base, quote, rate, diff_prev, pct_change, ma_7）。

    Returns:
        (新規件数, 更新件数) のタプル。
    """
    # ガード節
    if df.empty:
        return 0, 0

    # agg_rates のメタデータを取得
    engine = create_engine(config.DATABASE_URL)
    metadata = MetaData()
    table = Table("agg_rates", metadata, autoload_with=engine)

    df = df.copy()
    # DB格納のため date 列を datetime64 型から date 型に変換
    df["date"] = df["date"].dt.date
    # NaN → None 変換。先に object 型へ変換してから置換する。
    # float64 のまま where(..., None) すると、全行 NaN の列（履歴不足時の ma_7 など）は
    # None が nan に戻ってしまい、MySQL で "nan can not be used" エラーになるため。
    df = df.astype(object).where(pd.notnull(df), None)
    records = df.to_dict(orient="records")

    # UPSERT文
    stmt = insert(table).values(records)
    stmt = stmt.on_duplicate_key_update(
        rate=stmt.inserted.rate,
        diff_prev=stmt.inserted.diff_prev,
        pct_change=stmt.inserted.pct_change,
        ma_7=stmt.inserted.ma_7,
    )

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
    engine = create_engine(config.DATABASE_URL)
    df = read_raw_rates(engine)
    agg_df = compute_aggregates(df)
    inserted, updated = save_aggregates(agg_df)
    print(f"新規 {inserted} 件 / 更新 {updated} 件 を agg_rates に書き込みました")
