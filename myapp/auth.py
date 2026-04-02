from flask import Blueprint,request,jsonify
from .models import User
from . import db
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash


auth=Blueprint("auth",__name__)

@auth.route('/register',methods=['POST'])
def register():
    data=request.get_json()
    hashed_password=generate_password_hash(data['password'])

    new_user=User(
        username=data['username'],
        password=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"messag":"User registered successfully"}),201

@auth.route("/login",methods=['POST'])
def login():
    data=request.get_json()

    user=User.query.filter_by(username=data["username"]).first()

    if user and check_password_hash(user.password,data['password']):
        token=create_access_token(identity=user.id)
        return jsonify(access_token=token)

    return jsonify({"message":"Invalid credentials"}),401




