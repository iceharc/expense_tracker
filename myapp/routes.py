from flask import Blueprint,request,jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Expense
from __innit__ import db

main=Blueprint("main",__name__)

@main.route("/expenses",methods=['POST'])
@jwt_required()
def add_expense():
    user_id=get_jwt_identity()
    data=request.get_json()

    expense=Expense(
        amount=data['amount'],category=data['category'],
        description=data['description'],user_id=user_id
    )

    db.session.add(expense)
    db.session.commit()

    return jsonify({"message":"Expense added"}),201



@main.route("/expense",methods=["GET"])
@jwt_required()
def get_expenses():
    user_id=get_jwt_identity()
    expenses=Expense.query.filter_by(user_id=user_id).all()

    output=[]

    for expense in expenses:
        output.append({
            "id":expense.id,
            "id":expense.amount,
            "id":expense.category,
            "id":expense.description,
            "id":expense.date,
        })

    return jsonify(output)