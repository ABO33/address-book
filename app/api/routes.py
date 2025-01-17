import bcrypt
from flask import Blueprint, request, jsonify, current_app

from app import db
from app.models import User, Contact, Tag
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

api = Blueprint('api', __name__)

# Example: User registration endpoint
@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    db = current_app.extensions['sqlalchemy'].db
    bcrypt = current_app.extensions['flask_bcrypt']

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(email=data['email'], password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201


# User Login
@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        login_user(user)
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Login failed'}), 401

# User Profile
@api.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    if request.method == 'GET':
        return jsonify(current_user.to_dict())
    elif request.method == 'PUT':
        data = request.get_json()
        current_user.username = data.get('username', current_user.username)
        current_user.email = data.get('email', current_user.email)
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'})

# Contacts Endpoints
@api.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    if request.method == 'GET':
        contacts = Contact.query.filter_by(user_id=current_user.id).all()
        return jsonify([contact.to_dict() for contact in contacts])
    elif request.method == 'POST':
        data = request.get_json()
        contact = Contact(name=data['name'], phone=data['phone'], user_id=current_user.id)
        db.session.add(contact)
        db.session.commit()
        return jsonify({'message': 'Contact added successfully'}), 201

@api.route('/contacts/<int:contact_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403

    if request.method == 'PUT':
        data = request.get_json()
        contact.name = data.get('name', contact.name)
        contact.phone = data.get('phone', contact.phone)
        db.session.commit()
        return jsonify({'message': 'Contact updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'message': 'Contact deleted successfully'})

# Tags Endpoints
@api.route('/tags', methods=['GET', 'POST'])
@login_required
def tags():
    if request.method == 'GET':
        tags = Tag.query.filter_by(user_id=current_user.id).all()
        return jsonify([tag.to_dict() for tag in tags])
    elif request.method == 'POST':
        data = request.get_json()
        tag = Tag(name=data['name'], user_id=current_user.id)
        db.session.add(tag)
        db.session.commit()
        return jsonify({'message': 'Tag added successfully'}), 201

@api.route('/tags/<int:tag_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if tag.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403

    if request.method == 'PUT':
        data = request.get_json()
        tag.name = data.get('name', tag.name)
        db.session.commit()
        return jsonify({'message': 'Tag updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(tag)
        db.session.commit()
        return jsonify({'message': 'Tag deleted successfully'})

# Search Endpoint
@api.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '')
    results = Contact.query.filter(Contact.name.contains(query), Contact.user_id == current_user.id).all()
    return jsonify([result.to_dict() for result in results])
