from . import db
from flask_login import UserMixin
from sqlalchemy.types import JSON

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

    @staticmethod
    def bulk_create(data, user_id):
        contacts = []
        for item in data:
            contact = Contact(
                first_name=item.get('first_name'),
                last_name=item.get('last_name'),
                company_name=item.get('company_name'),
                address=item.get('address'),
                phone=item.get('phone'),
                email=item.get('email'),
                fax=item.get('fax'),
                mobile=item.get('mobile'),
                comment=item.get('comment'),
                user_id=user_id
            )
            contacts.append(contact)
        db.session.bulk_save_objects(contacts)
        db.session.commit()
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    fax = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    comment = db.Column(db.Text)  # Rich text field
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    custom_fields = db.Column(db.JSON, default={})  # JSON column for custom fields

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(20))  # Store color codes like #FF5733
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ContactTag(db.Model):
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)

