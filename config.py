# Konfigurace aplikace
import os

# Reset token – změňte na vlastní tajnou hodnotu
RESET_TOKEN = "tajny-token-20266"

# Otázka a možnosti odpovědí
QUESTION = "Jakou máš značku telefonu?"

OPTIONS = [
    {"id": "iphone",  "label": "a) iPhone"},
    {"id": "samsung", "label": "b) Samsung"},
    {"id": "huawei",  "label": "c) Huawei"},
    {"id": "xiaomi",  "label": "d) Xiaomi"},
    {"id": "jine",    "label": "e) Jiné"},
]

# Cesta k SQLite databázi – absolutní cesta relativní k tomuto souboru
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anketa.db")
