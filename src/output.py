import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import MetaData, Table, select

# 出力対象の通貨（基準通貨 EUR に対する quote）
TARGET_QUOTES = ["JPY", "USD"]
# 出力先ディレクトリ（.gitignore 済み）
OUTPUT_DIR = "data"

logger = logging.getLogger(__name__)


def read_agg_rates(engine, quotes: list[str] = TARGET_QUOTES) -> pd.DataFrame:
    """agg_rates から対象通貨の集計データを読み込む。

    Args:
        engine: SQLAlchemy の Engine。
        quotes: 読み込む対象の quote 通貨コードのリスト。

    Returns:
        対象通貨の集計データ（列: date, quote, rate, ma_7 など）。
    """
    # agg_rates のメタデータを取得し、グラフ出力に必要な列だけを対象通貨に絞って SELECT
    metadata = MetaData()
    table = Table("agg_rates", metadata, autoload_with=engine)
    stmt = select(table.c.date, table.c.quote, table.c.rate, table.c.ma_7).where(
        table.c.quote.in_(quotes)
    )

    with engine.connect() as conn:
        rows = conn.execute(stmt).all()
        df = pd.DataFrame(rows, columns=["date", "quote", "rate", "ma_7"])

    # date でソートし datetime64 に変換（時系列の折れ線描画を安定させるため）
    df = df.sort_values("date")
    df["date"] = pd.to_datetime(df["date"])

    return df


def export_csv(df: pd.DataFrame, path: str) -> None:
    """集計データを CSV ファイルに書き出す。

    Args:
        df: 出力する DataFrame。
        path: 出力先ファイルパス。
    """
    # 出力先ディレクトリを確保し、CSV を書き出す（Excel での文字化け対策に utf-8-sig）
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"件数:{len(df)}, パス:{path}")


def plot_rates(df: pd.DataFrame, path: str) -> None:
    """通貨ごとに rate の推移と7日移動平均を折れ線で描画し、PNG として保存する。

    Args:
        df: read_agg_rates の戻り値（複数通貨を含む）。
        path: 出力先 PNG パス。
    """
    # 通貨ごとに rate と ma_7 を1枚に重ねて描画。ラベルは文字化け回避のため英語表記。
    fig, ax = plt.subplots()
    for quote, g in df.groupby("quote"):
        ax.plot(g["date"], g["rate"], label=f"EUR/{quote}")
        ax.plot(g["date"], g["ma_7"], label=f"EUR/{quote} MA7", linestyle="--")
    ax.set_xlabel("date")
    ax.set_ylabel("rate")
    ax.set_title("EUR exchange rates")
    ax.legend()

    # バッチ実行なので show() は呼ばず、出力先を確保してから PNG 保存
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path)
    plt.close(fig)

    logger.info(f"パス:{path}")


# 動作確認用
if __name__ == "__main__":
    from sqlalchemy import create_engine

    import config

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    engine = create_engine(config.DATABASE_URL)

    df = read_agg_rates(engine)
    export_csv(df, os.path.join(OUTPUT_DIR, "agg_rates.csv"))
    plot_rates(df, os.path.join(OUTPUT_DIR, "rates.png"))
    print(f"CSV とグラフを {OUTPUT_DIR}/ に出力しました")
