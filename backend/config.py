import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:82512314dw@127.0.0.1:3306/couple_kitchen"
)
