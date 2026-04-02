from flask import Flask, jsonify, request
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, get_jwt_identity, jwt_required
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, User, Expense, Category
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)

# Config
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=90)

db.init_app(app)
jwt = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests"}), 429

# ------------------- Simple Routes -------------------
@app.route("/register", methods=["POST"])
@limiter.limit("3/minute")
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "User exists"}), 409
    user = User(username=data["username"], password=generate_password_hash(data["password"]))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered"}), 201

@app.route("/login", methods=["POST"])
@limiter.limit("5/minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    if user and check_password_hash(user.password, data["password"]):
        token = create_access_token(identity=str(user.id))
        return jsonify(access_token=token), 200
    return jsonify({"error": "Invalid credentials"}), 401

# ------------------- AI Insights -------------------
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

# ------------------- Autonomous AI Agent -------------------
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

# ------------------- Main -------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)