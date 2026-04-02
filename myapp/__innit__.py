from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .config import Config
from .models import User,Expense

db=SQLAlchemy()
jwt=JWTManager()
migrate=Migrate()

def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app,db)

    from .routes import main
    from .auth import auth
    
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app