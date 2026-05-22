import pandas as pd


def transform(raw_data):
    df = pd.DataFrame(raw_data)
    # dfの空チェック
    if df.empty:
        raise ValueError("データが空です")

    # dfの列不足チェック
    required = {"date", "base", "quote", "rate"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"必要な列に不足があります:{missing}")

    # チェックOK後の処理
    df["date"] = pd.to_datetime(df["date"])
    df["rate"] = df["rate"].astype(float)
    return df


# 動作確認用
if __name__ == "__main__":
    from src.extract import fetch_latest_rates

    rates = fetch_latest_rates()
    df = transform(rates)

    print(df)
    print(df.dtypes)
