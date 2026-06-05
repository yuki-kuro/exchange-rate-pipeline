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
    # HINT: load.py と同じく SQLAlchemy Core で書く。
    #   1) MetaData + Table("raw_rates", ..., autoload_with=engine) でテーブル定義を取得
    #   2) select(...) で集計に使う列だけ（date, base, quote, rate）を指定
    #   3) with engine.connect() as conn: rows = conn.execute(stmt).all()
    #   4) pd.DataFrame(rows, columns=[...]) で DataFrame 化（rows は Row のリスト）
    # HINT: date は DATE 型で返ってくる。後段で時系列ソートするので pd.to_datetime で datetime64 に変換しておくと rolling/diff が安定する。
    # Q: id, created_at は集計に使わない。select で最初から除くか（→ おすすめ）、全件取って後で落とすか。
    # TODO: 実装
    metadata = MetaData()
    table = Table("raw_rates", metadata, autoload_with=engine)
    stmt = select(table.c.date, table.c.base, table.c.quote, table.c.rate)
    with engine.connect() as conn:
        rows = conn.execute(stmt).all()
        df = pd.DataFrame(rows, columns=["date", "base", "quote", "rate"])
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
    # HINT: 前日比・移動平均は「同じ通貨ペアの時系列」に対して計算する必要がある。
    #       通貨ペアをまたいで diff() すると別通貨の値を引いてしまうので、必ず (base, quote) ごとに分けて計算する。
    # HINT: 流れの一例 —
    #   1) (base, quote, date) でソート
    #   2) groupby(["base", "quote"]) でペアごとに分け、各列を計算
    #        - diff_prev  : rate.diff()
    #        - pct_change : rate.pct_change()   ← (4) で「%」と決めたので *100 するか要検討（下の Q）
    #        - ma_7       : rate.rolling(window=7).mean()  ← min_periods 既定=window なので最初の6日は NaN（設計通り）
    # Q: pct_change を「%」で持つなら *100 が必要（0.012 → 1.2）。DDL の pct_change は % 前提。ここで *100 するか？
    # Q: groupby の戻りをどう元の df に書き戻すか（transform で列追加 / assign / concat など。やりやすい形でOK）。
    # TODO: 実装
    df_sorted = df.sort_values(["base", "quote", "date"], ascending=[True, True, True])
    # HINT: ❌ 計算対象の列が "date" になっている。前日比・移動平均は "rate" に対して計算する。
    #       diff()/pct_change() を "date"（datetime64）に適用すると、日付の差（timedelta）が出てしまう。
    df_sorted["diff_prev"] = df_sorted.groupby(["base", "quote"])["rate"].diff()
    # HINT: ❌ 代入先が "diff_prev" のまま（上の行を上書きしている）。これは pct_change の行なので別列に入れる。
    # HINT: ❌ ここも対象列は "rate"。さらに (4) の決定どおり「%」で持つなら *100 する（0.012 → 1.2）。
    df_sorted["pct_change"] = (
        df_sorted.groupby(["base", "quote"])["rate"].pct_change() * 100
    )
    # HINT: ⬜ ma_7（7日移動平均）が未実装。groupby + rolling で計算する。
    #       注意: groupby(...).rolling(7) は戻りが (group, 元index) の MultiIndex になり、そのまま代入すると行がズレる。
    #       transform を使うと元の行に揃ったまま計算できる:
    #         df_sorted.groupby(["base","quote"])["rate"].transform(lambda s: s.rolling(window=7).mean())
    #       （diff/pct_change も transform で書き方を揃えてもOK。min_periods 既定=window なので最初の6日は NaN）
    df_sorted["ma_7"] = df_sorted.groupby(["base", "quote"])["rate"].transform(
        lambda s: s.rolling(window=7).mean()
    )
    # HINT: ⬜ return が無い → 関数が None を返す。集計後の df_sorted を返す。
    #       列順は agg_rates に合わせて date, base, quote, rate, diff_prev, pct_change, ma_7。
    df_sorted = df_sorted[
        ["date", "base", "quote", "rate", "diff_prev", "pct_change", "ma_7"]
    ]
    return df_sorted


def save_aggregates(df: pd.DataFrame) -> tuple[int, int]:
    """集計結果を agg_rates テーブルへ UPSERT する。

    Args:
        df: compute_aggregates の戻り値
            （列: date, base, quote, rate, diff_prev, pct_change, ma_7）。

    Returns:
        (新規件数, 更新件数) のタプル。
    """
    # HINT: 基本構造は load.py の load_rates とほぼ同じ（autoload で agg_rates を取得 → UPSERT → 件数カウント）。
    #       異なるのは on_duplicate_key_update で更新する列が rate だけでなく diff_prev / pct_change / ma_7 も含む点。
    # HINT: ⚠️ NaN 対策 — diff_prev / pct_change / ma_7 は系列初日などで NaN になる。
    #       NaN のまま to_dict すると MySQL に NULL ではなく不正値が入る恐れがあるので、
    #       INSERT 前に NaN → None へ変換する（例: df.where(pd.notnull(df), None) など）。
    #       date 列の date 型変換も load.py と同様に必要。
    # TODO: ガード節（df.empty なら (0, 0)）
    # TODO: engine 作成 → agg_rates の Table を autoload
    # TODO: NaN→None・date 変換 → records 化
    # TODO: insert + on_duplicate_key_update（rate, diff_prev, pct_change, ma_7）
    # TODO: トランザクション内で既存キー取得 → UPSERT → 新規/更新件数を算出して返す
    # ガード節
    if df.empty:
        return 0, 0

    # agg_ratesテーブルのメタデータを取得
    engine = create_engine(config.DATABASE_URL)
    metadata = MetaData()
    table = Table("agg_rates", metadata, autoload_with=engine)

    # NaN → None 変換、datetime64型 → date型 変換
    df = df.copy()
    df["date"] = df["date"].dt.date
    # HINT: 先に object 型へ変換してから None を入れる。
    #       float64 のまま where(..., None) すると、全行 NaN の列（例: 履歴不足時の ma_7）は
    #       None が nan に戻ってしまい、MySQL で "nan can not be used" エラーになる。
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
