import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    RATELIMIT_DEFAULT = '200/hour;10/minute'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
