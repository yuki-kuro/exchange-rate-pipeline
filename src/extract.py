import requests
import config


def fetch_latest_rates():
    url = f"{config.FRANKFURTER_API_URL}/rates"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"為替レートの取得に失敗しました: {e}")
        raise


# 動作確認用
if __name__ == "__main__":
    rates = fetch_latest_rates()
    print(rates)
