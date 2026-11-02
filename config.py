import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tourism-vista-secret-key-academic-dw-2026')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Dataset path
    DATA_CSV_PATH = os.environ.get('DATA_CSV_PATH', str(BASE_DIR / 'data' / 'tourism_dataset.csv'))
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', str(BASE_DIR / 'data' / 'tourism_warehouse.db'))
    
    # Database Configuration (MySQL credentials with SQLite fallback)
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite').lower()  # 'mysql' or 'sqlite'
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'tourism_warehouse')
    
    @classmethod
    def get_sqlalchemy_database_uri(cls):
        if cls.DB_TYPE == 'mysql' and cls.DB_USER:
            # MySQL connection URI
            pwd = f":{cls.DB_PASSWORD}" if cls.DB_PASSWORD else ""
            return f"mysql+pymysql://{cls.DB_USER}{pwd}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4"
        return f"sqlite:///{cls.SQLITE_DB_PATH}"
