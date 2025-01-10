from sqlite3 import IntegrityError

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from flask_login import current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import func

from ..models import db, Contact, Tag, ContactTag
from ..forms import ContactForm, ProfileForm
from ..utils import process_csv, process_json, process_excel
from . import main


@main.route('/')
@login_required
def home():
    return render_template('main/home.html', user=current_user)


@main.route('/add_contact', methods=['GET', 'POST'])
@login_required
def add_contact():
    form = ContactForm()
    tags = Tag.query.filter_by(user_id=current_user.id).all()

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
        # Assign selected tags
        selected_tags = request.form.getlist('tags')
        for tag_id in selected_tags:
            tag = Tag.query.get(tag_id)
            if tag:
                contact.tags.append(tag)

        db.session.add(contact)
        db.session.commit()
        flash('Contact saved successfully!', 'success')
        return redirect(url_for('main.contacts'))

    return render_template('main/add_contact.html', form=form, tags=tags)


@main.route('/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    if request.method == 'POST':
        name = request.form['name']
        color = request.form.get('color', '#FFFFFF')  # Default color white
        parent_id = request.form.get('parent_id')
        parent_id = int(parent_id) if parent_id else None

        tag = Tag(name=name, color=color, parent_id=parent_id, user_id=current_user.id)

        try:
            db.session.add(tag)
            db.session.commit()
            flash('Tag added successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Tag name must be unique.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding tag: {e}', 'danger')

    tags = Tag.query.filter_by(user_id=current_user.id).all()
    return render_template('main/tags.html', tags=tags)

@main.route('/delete_tag/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if tag.user_id != current_user.id:
        abort(403)

    try:
        db.session.delete(tag)
        db.session.commit()
        flash('Tag deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting tag: {e}', 'danger')

    return redirect(url_for('main.manage_tags'))

@main.route('/filter_contacts', methods=['GET'])
@login_required
def filter_contacts():
    tag_id = request.args.get('tag_id', type=int)
    if tag_id:
        # Filter contacts by tag
        contacts = (
            Contact.query.join(ContactTag)
            .filter(ContactTag.tag_id == tag_id, Contact.user_id == current_user.id)
            .all()
        )
    else:
        # No tag selected, show all contacts
        contacts = Contact.query.filter_by(user_id=current_user.id).all()

    tags = Tag.query.filter_by(user_id=current_user.id).all()
    return render_template('main/contacts.html', contacts=contacts, tags=tags)


@main.route('/contacts', methods=['GET'])
@login_required
def contacts():
    user_contacts = Contact.query.filter_by(user_id=current_user.id).all()
    tags = Tag.query.filter_by(user_id=current_user.id).all()
    return render_template('main/contacts.html', contacts=user_contacts, tags=tags)

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
    tags = Tag.query.filter_by(user_id=current_user.id).all()  # Fetch all tags for the user

    if request.method == 'POST':
        # Handle custom field addition or update
        field_name = request.form.get('name')
        field_value = request.form.get('value')

        if field_name and field_value:
            # Initialize custom fields if not present
            if not contact.custom_fields:
                contact.custom_fields = {}
            # Add or update the custom field
            contact.custom_fields[field_name] = field_value
            db.session.commit()
            flash('Custom field updated successfully!', 'success')

        # Handle form submission for other fields and tag assignment
        if form.validate_on_submit():
            form.populate_obj(contact)

            # Update tags assigned to the contact
            selected_tags = request.form.getlist('tags')
            contact.tags = []  # Clear existing tags
            for tag_id in selected_tags:
                tag = Tag.query.get(tag_id)
                if tag:
                    contact.tags.append(tag)

            db.session.commit()
            flash('Contact updated successfully!', 'success')
            return redirect(url_for('main.view_contact', contact_id=contact.id))

    custom_fields = contact.custom_fields.items() if contact.custom_fields else []
    return render_template('main/edit_contact.html', form=form, contact=contact, custom_fields=custom_fields, tags=tags)


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
        if not file:
            flash('No file uploaded. Please upload a valid file.', 'warning')
            return redirect(url_for('main.import_data'))

        data = None
        if file.filename.endswith('.csv'):
            data = process_csv(file)
        elif file.filename.endswith('.json'):
            data = process_json(file)
        elif file.filename.endswith('.xls') or file.filename.endswith('.xlsx'):
            data = process_excel(file)
        else:
            flash('Unsupported file format. Please upload a CSV, JSON, or Excel file.', 'danger')
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

    # Query for most common tags based on usage in contacts
    most_common_tags = (
        db.session.query(Tag, func.count(ContactTag.contact_id).label('usage_count'))
        .join(ContactTag, ContactTag.tag_id == Tag.id)
        .join(Contact, Contact.id == ContactTag.contact_id)
        .filter(Tag.user_id == current_user.id)
        .group_by(Tag.id)
        .order_by(func.count(ContactTag.contact_id).desc())
        .limit(10)  # Limit to top 10 most common tags
        .all()
    )

    # Extract tag IDs for filtering contacts
    most_common_tag_ids = [tag.id for tag, _ in most_common_tags]

    # Fetch contacts associated with the most common tags
    contacts = (
        Contact.query.join(ContactTag)
        .filter(ContactTag.tag_id.in_(most_common_tag_ids), Contact.user_id == current_user.id)
        .all()
    )

    return render_template(
        'main/contacts.html',
        contacts=contacts,
        tags=[tag for tag, _ in most_common_tags]  # Pass only the tags
    )

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
