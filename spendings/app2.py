from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    JWTManager,
    get_jwt_identity,
    jwt_required
)
import os
from dotenv import load_dotenv
load_dotenv()
import numpy as np
from sklearn.linear_model import LinearRegression
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import db, User, Expense, Category


app = Flask(__name__)

# ---------------- CONFIG ----------------

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=90)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

db.init_app(app)
jwt = JWTManager(app)

# ---------------- RATE LIMITER ----------------

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# ---------------- RATE LIMIT ERROR ----------------

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Too many requests",
        "message": "You are sending requests too fast. Please slow down."
    }), 429


# ---------------- REGISTER ----------------

@app.route("/register", methods=['POST'])
@limiter.limit("3 per minute")
def register():

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'])

    new_user = User(
        username=data['username'],
        password=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"Message": "Registered Successfully"}), 201


# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])

def login():

    data = request.get_json()

    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        token = create_access_token(identity=str(user.id))
        return jsonify(access_token=token), 200

    return jsonify({"Message": "Invalid credentials"}), 401


# ---------------- PROFILE ----------------

@app.route("/profile", methods=['GET'])
@jwt_required()

def profile():

    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"Message": "User not found"}), 404

    return jsonify({"user_id": current_user_id}), 200


# ---------------- CREATE EXPENSE ----------------

@app.route("/expense", methods=["POST"])
@jwt_required()
@limiter.limit("20 per minute")
def create_expense():

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    data = request.get_json()

    # expense data
    title = data.get('title')
    amount = data.get('amount')
    date = data.get('date')

    # category data
    category_data = data.get('category')
    category_name = category_data.get("name")
    category_description = category_data.get("description")

    # check if category exists
    category = Category.query.filter_by(
        name=category_name,
        user_id=user_id
    ).first()

    # create category if it doesn't exist
    if not category:
        category = Category(
            name=category_name,
            description=category_description,
            user_id=user_id
        )

        db.session.add(category)
        db.session.commit()

    # create expense
    new_expense = Expense(
        title=title,
        amount=amount,
        date=date,
        user_id=user_id,
        category_id=category.id
    )

    db.session.add(new_expense)
    db.session.commit()

    return jsonify({
        "message": "Expense created successfully",
        "expense": {
            "id": new_expense.id,
            "title": new_expense.title,
            "amount": new_expense.amount,
            "date": new_expense.date,
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description
            }
        }
    }), 200


# ---------------- GET EXPENSES ----------------

@app.route("/expenses", methods=["GET"])
@jwt_required()
@limiter.limit("60 per minute")
def get_expenses():

    user_id = int(get_jwt_identity())

    expenses = Expense.query.filter_by(user_id=user_id).all()

    result = []

    for expense in expenses:

        result.append({
            "id": expense.id,
            "title": expense.title,
            "amount": expense.amount,
            "date": expense.date,
            "category": {
                "id": expense.category.id if expense.category else None,
                "name": expense.category.name if expense.category else None,
                "description": expense.category.description if expense.category else None
            }
        })

    return jsonify(result), 200
@app.route("/ai-insights", methods=["GET"])
@jwt_required()
@limiter.limit("10/minute")
def ai_insights():
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).all()
    if not expenses:
        return jsonify({"message": "No expenses"}), 200
    total_spent = sum(e.amount for e in expenses)
    categories = {}
    for e in expenses:
        name = e.category.name if e.category else "Uncategorized"
        categories[name] = categories.get(name, 0) + e.amount
    highest_category = max(categories, key=categories.get)
    avg_spending = total_spent / len(expenses)
    suggestion = f"You spend most on {highest_category}. Consider reducing it."
    return jsonify({
        "total_spent": total_spent,
        "average_spending": round(avg_spending,2),
        "highest_category": highest_category,
        "category_breakdown": categories,
        "suggestion": suggestion
    }), 200

# ------------------- Predict Spending -------------------
@app.route("/predict-spending", methods=["GET"])
@jwt_required()
@limiter.limit("10/minute")
def predict_spending():
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).all()
    if len(expenses) < 3:
        return jsonify({"message": "Not enough data"}), 400
    X = np.array([[i] for i in range(len(expenses))])
    y = np.array([e.amount for e in expenses])
    model = LinearRegression().fit(X, y)
    predicted = model.predict(np.array([[len(expenses)]]))[0]
    return jsonify({"predicted_next_expense": round(float(predicted),2)}), 200

@app.route("/ai-agent", methods=["GET"])
@jwt_required()
@limiter.limit("5/minute")
def ai_agent():
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).all()
    if len(expenses) < 3:
        return jsonify({"message": "Not enough data"}), 400
    category_totals = {}
    for e in expenses:
        name = e.category.name if e.category else "Uncategorized"
        category_totals.setdefault(name, []).append(e.amount)
    alerts, recommendations = [], []
    for cat, amounts in category_totals.items():
        avg = sum(amounts)/len(amounts)
        last = amounts[-1]
        if last > avg * 1.5:
            alerts.append(f"Alert: Latest {cat} expense ({last}) > avg ({round(avg,2)})")
            recommendations.append(f"Consider reviewing {cat} spending.")
    total_spent = sum([sum(v) for v in category_totals.values()])
    avg_spent = total_spent/len(expenses)
    alerts.append(f"Total spent: {total_spent}, average per expense: {round(avg_spent,2)}")
    return jsonify({"alerts": alerts, "recommendations": recommendations}), 200
# ---------------- MAIN ----------------

if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(debug=True)