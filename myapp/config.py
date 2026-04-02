import os

class Config:
    SECRET_KEY=os.getenv("SECRET_KEY",'supersecret')
    SQLALCHEMY_DATABASE_URI="sqlite:///expenses.db"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY","jwtsecret")