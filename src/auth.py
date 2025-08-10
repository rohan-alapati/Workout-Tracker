# src/auth.py
from flask import Blueprint, request, jsonify
from src.model import db, User
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify(msg="Email and password required"), 400

    if User.query.filter_by(email=email).first():
        return jsonify(msg="Email already registered"), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User login
    ---
    tags: [Auth]
    consumes:
      - application/json
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email:    {type: string, example: alice@example.com}
            password: {type: string, example: s3cret}
    responses:
      200:
        description: JWT issued
        schema:
          type: object
          properties:
            access_token: {type: string}
      401:
        description: Bad email or password
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(msg="Bad email or password"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(str(user_id))
    return jsonify(id=user.id, email=user.email), 200
