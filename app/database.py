# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "gpp_db_pdftest"

settings = Settings()

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
