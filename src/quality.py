def check_quality(df):
    # rateの欠損値チェックと0以下チェック
    bad = (df["rate"].isna()) | (df["rate"] <= 0)
    # 不正行があれば表示
    if bad.any():
        print("不正行ありdf: ")
        print(df[bad])

    return df[~bad]


# 動作確認用
if __name__ == "__main__":
    from src.extract import fetch_latest_rates
    from src.transform import transform

    rates = fetch_latest_rates()
    df = transform(rates)

    clean_df = check_quality(df)
    print("クレンジング(不正行除外)後df:")
    print(clean_df)
