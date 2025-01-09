from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from ..models import db, Contact, Tag, ContactTag
from ..forms import ContactForm, ProfileForm
from ..utils import process_csv, process_json
from . import main


@main.route('/')
@login_required
def home():
    return render_template('main/home.html', user=current_user)


@main.route('/add_contact', methods=['GET', 'POST'])
@login_required
def add_contact():
    form = ContactForm()
    if form.validate_on_submit():
        contact = Contact(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            company_name=form.company_name.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            fax=form.fax.data,
            mobile=form.mobile.data,
            comment=form.comment.data,
            user_id=current_user.id
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact saved successfully!', 'success')
        return redirect(url_for('main.home'))
    return render_template('main/add_contact.html', form=form)


@main.route('/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color')
        if name and color:
            new_tag = Tag(name=name, color=color, user_id=current_user.id)
            db.session.add(new_tag)
            db.session.commit()
            flash('Tag added successfully!')
        return redirect(url_for('main.manage_tags'))
    tags = Tag.query.filter_by(user_id=current_user.id).all()
    return render_template('main/manage_tags.html', tags=tags)


@main.route('/delete_tag/<int:tag_id>')
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get(tag_id)
    if tag and tag.user_id == current_user.id:
        db.session.delete(tag)
        db.session.commit()
        flash('Tag deleted successfully!')
    return redirect(url_for('main.manage_tags'))


@main.route('/contacts', methods=['GET'])
@login_required
def contacts():
    user_contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('main/contacts.html', contacts=user_contacts)


@main.route('/view_contact/<int:contact_id>', methods=['GET'])
@login_required
def view_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        abort(403)
    return render_template('main/view_contact.html', contact=contact)


@main.route('/edit_contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        abort(403)

    form = ContactForm(obj=contact)

    # Handle adding or updating custom fields
    if request.method == 'POST':
        # Add or update custom field
        field_name = request.form.get('name')
        field_value = request.form.get('value')

        if field_name and field_value:
            # Add or update custom field in the contact's custom_fields JSON
            if not contact.custom_fields:
                contact.custom_fields = {}  # Initialize if not already present

            # Update the custom field value
            contact.custom_fields[field_name] = field_value
            db.session.commit()  # Commit the change to the database
            flash('Custom field updated successfully!', 'success')

        # Handling contact form submission (update other fields)
        if form.validate_on_submit():
            form.populate_obj(contact)
            db.session.commit()
            flash('Contact updated successfully!', 'success')
            return redirect(url_for('main.view_contact', contact_id=contact.id))

    custom_fields = contact.custom_fields.items() if contact.custom_fields else []

    return render_template('main/edit_contact.html', form=form, contact=contact, custom_fields=custom_fields)


@main.route('/delete_contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        abort(403)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('main.contacts'))


@main.route('/import', methods=['GET', 'POST'])
@login_required
def import_data():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            data = process_csv(file)
        elif file and file.filename.endswith('.json'):
            data = process_json(file)
        else:
            flash('Unsupported file format. Please upload a CSV or JSON file.', 'danger')
            return redirect(url_for('main.import_data'))

        if data:
            try:
                Contact.bulk_create(data, user_id=current_user.id)
                flash('Contacts imported successfully!', 'success')
            except Exception as e:
                flash(f'Error importing data: {str(e)}', 'danger')
        else:
            flash('No valid data found in the file.', 'warning')
        return redirect(url_for('main.contacts'))

    return render_template('main/import.html')


from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        print("Form submitted and validated!")
        try:
            # Update user details
            current_user.username = form.username.data
            current_user.email = form.email.data

            if form.password.data:
                print("Updating password")
                current_user.password = generate_password_hash(form.password.data)

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            print("Profile updated in DB")
        except Exception as e:
            db.session.rollback()
            print(f"Error during commit: {str(e)}")
            flash('Error updating profile!', 'danger')

        return redirect(url_for('main.profile'))

    else:
        if form.errors:
            print("Form validation errors:", form.errors)

    return render_template('main/profile.html', form=form)

@main.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # Delete the user and all associated data
    db.session.delete(current_user)
    db.session.commit()
    flash('Account deleted successfully.', 'success')
    return redirect(url_for('main.home'))  # Redirect to home or login page

@main.route('/contacts/all', methods=['GET'])
@login_required
def all_contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('main/contacts.html', contacts=contacts)

@main.route('/contacts/most_common_tags', methods=['GET'])
@login_required
def most_common_tags():
    from sqlalchemy import func
    tags = db.session.query(Contact.company_name, func.count(Contact.company_name).label('count')) \
        .filter(Contact.user_id == current_user.id) \
        .group_by(Contact.company_name) \
        .order_by(func.count(Contact.company_name).desc()).all()
    return render_template('main/contacts.html', tags=tags)

@main.route('/contacts/same_firstnames', methods=['GET'])
@login_required
def same_firstnames():
    from sqlalchemy import and_
    contacts = db.session.query(Contact).filter(
        and_(
            Contact.first_name.in_(
                db.session.query(Contact.first_name)
                .group_by(Contact.first_name)
                .having(func.count(Contact.first_name) > 1)
            ),
            Contact.user_id == current_user.id
        )
    ).all()
    return render_template('main/contacts.html', contacts=contacts)

@main.route('/contacts/same_lastnames', methods=['GET'])
@login_required
def same_lastnames():
    from sqlalchemy import and_
    contacts = db.session.query(Contact).filter(
        and_(
            Contact.last_name.in_(
                db.session.query(Contact.last_name)
                .group_by(Contact.last_name)
                .having(func.count(Contact.last_name) > 1)
            ),
            Contact.user_id == current_user.id
        )
    ).all()
    return render_template('main/contacts.html', contacts=contacts)

@main.route('/contacts/search', methods=['GET', 'POST'])
@login_required
def search_contact():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        contact = Contact.query.filter_by(first_name=first_name, last_name=last_name, user_id=current_user.id).first()
        return render_template('main/contacts.html', contacts=[contact] if contact else [], search=True)
    return render_template('main/search.html')  # Render a form for the user to enter name and last name
