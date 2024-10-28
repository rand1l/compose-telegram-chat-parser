import os


class Config:
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    SESSION_NAME = os.getenv('SESSION_NAME')
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres/{os.getenv('POSTGRES_DB')}"
