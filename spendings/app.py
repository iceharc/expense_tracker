from flask import Flask, jsonify, request
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    JWTManager,
    get_jwt_identity,
    jwt_required
)
from models import db, User, Expense, Category

app = Flask(__name__)


app.config['JWT_SECRET_KEY'] = 'this-is-a-very-long-super-secure-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=90)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
db.init_app(app)
jwt = JWTManager(app)


@app.route("/register", methods=['POST'])
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


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        token = create_access_token(identity=str(user.id))
        return jsonify(access_token=token), 200

    return jsonify({"Message": "Invalid credentials"}), 401


@app.route("/profile", methods=['GET'])
@jwt_required()
def profile():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"Message": "User not found"}), 404

    return jsonify({"user_id": current_user_id}), 200


#creating the expense creation route
@app.route("/expense",methods=["POST"])
@jwt_required()
def create_expense():
    user_id=int(get_jwt_identity())
    user=User.query.get(user_id)
    data=request.get_json()
    #expense data
    title=data.get('title')
    amount=data.get('amount')
    date=data.get('date')
    print(date)
    #category data
    category_data=data.get('category')
    category_name=category_data.get("name")
    category_description=category_data.get("description")

    #check if the category exists for the user
    category=Category.query.filter_by(name=category_name,user_id=user_id).first()

    #if not category create a new one
    if not category:
        category=Category(
            name=category_name,
            description=category_description,
            user_id=user_id
        )
        db.session.add(category)
        
    
    #create a new expense
    new_expense=Expense(
        title=title,amount=amount,date=date,user_id=user_id,category_id=category.id
    )

    db.session.add(new_expense)
    db.session.commit()

    return jsonify({
        "message":"Expense creates succesfully",
        "expense":{
            "id":new_expense.id,
            "title":new_expense.title,
            "amount":new_expense.amount,
            "date":new_expense.date,
            "category":{
                "id":category.id,
                "name":category.name,
                "description":category.description
            }
        }
    }),200


@app.route("/expenses", methods=["GET"])
@jwt_required()
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










if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
