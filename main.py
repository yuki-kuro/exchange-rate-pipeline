import logging
import os

from sqlalchemy import create_engine

import config
from src import aggregate, extract, load, output, quality, transform

logger = logging.getLogger(__name__)


def main():
    """ETL パイプライン全体を実行する。

    Extract → Transform → 品質チェック → Load(raw) → 集計 → 出力(CSV/PNG)
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    # 集計・出力は DB を経由する設計。engine は1つ作って使い回す。
    engine = create_engine(config.DATABASE_URL)

    logger.info("-----パイプライン開始-----")

    # Extract → Transform → 品質チェック
    rates = extract.fetch_latest_rates()
    logger.info("Extract 完了: レート取得")

    df = transform.transform(rates)
    logger.info("Transform 完了: %d件", len(df))

    before = len(df)
    df = quality.check_quality(df)
    logger.info("品質チェック 完了: %d件（除外 %d件）", len(df), before - len(df))

    # Load（raw_rates へ保存）
    inserted, updated = load.load_rates(df)
    logger.info("Load 完了: 新規%d 更新%d", inserted, updated)

    # 集計（raw_rates → agg_rates）
    df = aggregate.read_raw_rates(engine)
    agg_df = aggregate.compute_aggregates(df)
    inserted, updated = aggregate.save_aggregates(agg_df)
    logger.info("集計 完了: 新規%d 更新%d", inserted, updated)

    # 出力（agg_rates → CSV / PNG）
    df = output.read_agg_rates(engine)
    output.export_csv(df, os.path.join(output.OUTPUT_DIR, "agg_rates.csv"))
    output.plot_rates(df, os.path.join(output.OUTPUT_DIR, "rates.png"))

    logger.info("-----パイプライン完了-----")


if __name__ == "__main__":
    main()
