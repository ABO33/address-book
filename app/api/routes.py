from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, Contact, Tag, ContactTag, User
from app.utils import process_csv, process_json, process_excel
from sqlalchemy.exc import IntegrityError

api = Blueprint('api', __name__)

@api.route('/login', methods=['POST'])
def login():
    """API endpoint for logging in a user."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({"success": True, "message": "Login successful", "user": {"id": user.id, "email": user.email, "username": user.username}})
    return jsonify({"success": False, "error": "Invalid email or password"}), 401

@api.route('/register', methods=['POST'])
def register():
    """API endpoint for registering a new user."""
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "Email already registered"}), 400

    new_user = User(email=email, username=username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"success": True, "message": "Registration successful", "user": {"id": new_user.id, "email": new_user.email, "username": new_user.username}}), 201

@api.route('/logout', methods=['POST'])
def logout():
    """API endpoint for logging out a user."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "No user is logged in"}), 400

    logout_user()
    return jsonify({"success": True, "message": "Logout successful"})

@api.route('/home', methods=['GET'])
@login_required
def home():
    """API endpoint for home route."""
    return jsonify({"success": True, "message": "Welcome to the Contacts API", "user": {"id": current_user.id, "email": current_user.email}})

@api.route('/contacts', methods=['POST'])
@login_required
def add_contact():
    """API endpoint to add a contact."""
    data = request.get_json()
    contact = Contact(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        company_name=data.get('company_name'),
        address=data.get('address'),
        phone=data.get('phone'),
        email=data.get('email'),
        fax=data.get('fax'),
        mobile=data.get('mobile'),
        comment=data.get('comment'),
        user_id=current_user.id
    )

    tag_ids = data.get('tags', [])
    for tag_id in tag_ids:
        tag = Tag.query.get(tag_id)
        if tag:
            contact.tags.append(tag)

    try:
        db.session.add(contact)
        db.session.commit()
        return jsonify({"success": True, "message": "Contact added successfully!", "contact": contact.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to add contact: {e}"}), 400

@api.route('/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    """API endpoint to manage tags."""
    if request.method == 'POST':
        data = request.get_json()
        tag = Tag(
            name=data.get('name'),
            color=data.get('color', '#FFFFFF'),
            parent_id=data.get('parent_id'),
            user_id=current_user.id
        )

        try:
            db.session.add(tag)
            db.session.commit()
            return jsonify({"success": True, "message": "Tag added successfully!", "tag": tag.to_dict()}), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"success": False, "error": "Tag name must be unique."}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Failed to add tag: {e}"}), 400

    tags = Tag.query.filter_by(user_id=current_user.id).all()
    return jsonify({"success": True, "tags": [tag.to_dict() for tag in tags]})

@api.route('/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id):
    """API endpoint to delete a tag."""
    tag = Tag.query.get_or_404(tag_id)
    if tag.user_id != current_user.id:
        abort(403)

    try:
        db.session.delete(tag)
        db.session.commit()
        return jsonify({"success": True, "message": "Tag deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete tag: {e}"}), 400

@api.route('/contacts/filter', methods=['GET'])
@login_required
def filter_contacts():
    """API endpoint to filter contacts by tag."""
    tag_id = request.args.get('tag_id', type=int)
    if tag_id:
        contacts = (
            Contact.query.join(ContactTag)
            .filter(ContactTag.tag_id == tag_id, Contact.user_id == current_user.id)
            .all()
        )
    else:
        contacts = Contact.query.filter_by(user_id=current_user.id).all()

    return jsonify({"success": True, "contacts": [contact.to_dict() for contact in contacts]})

@api.route('/contacts', methods=['GET'])
@login_required
def list_contacts():
    """API endpoint to list all contacts."""
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return jsonify({"success": True, "contacts": [contact.to_dict() for contact in contacts]})

@api.route('/contacts/<int:contact_id>', methods=['GET'])
@login_required
def view_contact(contact_id):
    """API endpoint to view a specific contact."""
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        abort(403)
    return jsonify({"success": True, "contact": contact.to_dict()})

@api.route('/contacts/<int:contact_id>', methods=['PUT'])
@login_required
def edit_contact(contact_id):
    """API endpoint to edit a contact."""
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        abort(403)

    data = request.get_json()
    contact.first_name = data.get('first_name', contact.first_name)
    contact.last_name = data.get('last_name', contact.last_name)
    contact.company_name = data.get('company_name', contact.company_name)
    contact.address = data.get('address', contact.address)
    contact.phone = data.get('phone', contact.phone)
    contact.email = data.get('email', contact.email)
    contact.fax = data.get('fax', contact.fax)
    contact.mobile = data.get('mobile', contact.mobile)
    contact.comment = data.get('comment', contact.comment)

    tag_ids = data.get('tags', [])
    contact.tags = [Tag.query.get(tag_id) for tag_id in tag_ids if Tag.query.get(tag_id)]

    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Contact updated successfully!", "contact": contact.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to update contact: {e}"}), 400

@api.route('/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    """API endpoint to delete a contact."""
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        abort(403)

    try:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({"success": True, "message": "Contact deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete contact: {e}"}), 400

@api.route('/contacts/import', methods=['POST'])
@login_required
def import_contacts():
    """API endpoint to import contacts."""
    file = request.files.get('file')
    if not file:
        return jsonify({"success": False, "error": "No file uploaded."}), 400

    data = None
    if file.filename.endswith('.csv'):
        data = process_csv(file)
    elif file.filename.endswith('.json'):
        data = process_json(file)
    elif file.filename.endswith(('.xls', '.xlsx')):
        data = process_excel(file)
    else:
        return jsonify({"success": False, "error": "Unsupported file format."}), 400

    if data:
        try:
            Contact.bulk_create(data, user_id=current_user.id)
            return jsonify({"success": True, "message": "Contacts imported successfully!"}), 201
        except Exception as e:
            return jsonify({"success": False, "error": f"Error importing contacts: {e}"}), 400
    return jsonify({"success": False, "error": "No valid data found in the file."}), 400

@api.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """API endpoint to get or update user profile."""
    if request.method == 'PUT':
        data = request.get_json()
        current_user.username = data.get('username', current_user.username)
        current_user.email = data.get('email', current_user.email)
        if data.get('password'):
            current_user.password = generate_password_hash(data['password'])

        try:
            db.session.commit()
            return jsonify({"success": True, "message": "Profile updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Failed to update profile: {e}"}), 400

    return jsonify({"success": True, "user": {"username": current_user.username, "email": current_user.email}})

@api.route('/delete_account', methods=['DELETE'])
@login_required
def delete_account():
    """API endpoint to delete the user account."""
    try:
        db.session.delete(current_user)
        db.session.commit()
        return jsonify({"success": True, "message": "Account deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete account: {e}"}), 400
