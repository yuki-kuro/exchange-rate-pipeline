import os
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# MySQLへの接続URLを.envの値から組み立てる
DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
)

# Frankfurter APIのベースURL
FRANKFURTER_API_URL = "https://api.frankfurter.dev/v2"
