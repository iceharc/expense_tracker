from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()


class User(db.Model):
    id=db.Column(db.Integer,primary_key=True,unique=True)
    username=db.Column(db.String,unique=True,nullable=False)
    password=db.Column(db.String,nullable=False)
    
    expenses=db.relationship("Expense",backref='user',lazy=True)
   
class Expense(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String,nullable=False)
    amount=db.Column(db.Float,nullable=False)
    date=db.Column(db.String,nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    category_id=db.Column(db.Integer,db.ForeignKey('category.id'))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)  
    description = db.Column(db.String,nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    expense = db.relationship('Expense', backref='category', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='unique_user_category'),
    )
