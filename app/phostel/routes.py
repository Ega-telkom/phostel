from flask import Flask, request, render_template, redirect, url_for, render_template_string, send_from_directory, abort, Blueprint, current_app, abort
import os
from PIL import Image as PILImage
import mimetypes
from flask_login import login_required, current_user
import sqlite3
from werkzeug.utils import secure_filename
import uuid
from sqlalchemy import Column, String, ForeignKey, or_, and_
from sqlalchemy.orm import relationship
import uuid
from app import db
import time
from datetime import datetime
from app.auth.routes import User
import humanize

# konfigurasi
phostel = Blueprint('phostel', __name__)

class Image(db.Model):
    __tablename__ = 'image'
    id = db.Column(db.String(36), primary_key=True)  # UUID
    filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120))
    filepath = db.Column(db.String(120), nullable=False)
    tag = db.Column(db.String)
    like = db.Column(db.Integer, default=0)
    upload_date = db.Column(db.Integer, default=lambda: int(time.time()))

    # Foreign key referencing the User model
    user_id = Column(db.String(36), ForeignKey('user.id'), nullable=False)

    # Relationship to User model
    user = relationship('User', back_populates='images')

    __table_args__ = (db.UniqueConstraint('user_id', 'id', name='_user_image_uc'),)

class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    image_id = db.Column(db.String(36), db.ForeignKey('image.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'image_id', name='_user_image_uc'),
    )

@phostel.route('/')
def index():
    image = Image.query.order_by(Image.upload_date.desc()).all()
    images = [{'id': img.id, 'filename': img.filename, 'title': img.title} for img in image]

    auth = current_user.is_authenticated
    
    # bangun html untuk menampilkan gambar
    return render_template('index.html', images=images, auth=auth, current_user=current_user)

@phostel.route('/upload')
@login_required
def upload():
    auth = current_user.is_authenticated
    return render_template('upload.html', auth=auth, current_user=current_user)

@phostel.route('/phostel/<uuid:item_id>')
def images(item_id):
    image = Image.query.get(str(item_id))

    image_path = os.path.join(os.getcwd(), 'static', 'uploads', image.filename)

    try:
        with PILImage.open(image_path) as img:
            width, height = img.size
    except Exception as e:
        return f"Error opening image: {e}", 500

    if not image:
        abort(404)
    
    auth = current_user.is_authenticated
    
    user = image.user
    user_img = Image.query.filter(Image.user_id == user.id, Image.id != image.id).all()

    humanize.i18n.activate("id_ID")
    humanized_time = humanize.naturaltime(datetime.fromtimestamp(image.upload_date))
    liked = False
    if current_user.is_authenticated:
        liked = Like.query.filter_by(user_id=current_user.id, image_id=image.id).first() is not None

    like_count = Like.query.filter_by(image_id=image.id).count()

    return render_template('gambar.html', image=image, humanized_time=humanized_time, images=user_img, auth=auth, user=user, current_user=current_user, tags=image.tag, liked=liked, like_count=like_count, dimen={'width': width, 'height': height})

@phostel.route('/u/<user_id>')
def user(user_id):
    user = User.query.get(user_id)
    if not user:
        return render_template('404.html'), 404
    
    auth = current_user.is_authenticated

    humanize.i18n.activate("id_ID")
    humanized_time = humanize.naturaltime(datetime.fromtimestamp(user.birth))

    images = Image.query.filter_by(user_id=user_id).all()
    upload_count = Image.query.filter_by(user_id=user.id).count()

    owner = current_user.is_authenticated and current_user.id == user_id

    return render_template('user.html', user=user, images=images, owner=owner, upload_count=upload_count, auth=auth, humanized_time=humanized_time)

@phostel.route('/s')
def search():
    query = request.args.get('q', '').strip()
    filters = []

    user = User.query.all()

    auth = current_user.is_authenticated

    if not query:
        return redirect(url_for('phostel.index'))  # or just render the search form again
    else:
        keywords = query.split()

        # Search using full phrase first
        phrase_filter = or_(
            Image.title.ilike(f'%{query}%'),
            Image.tag.ilike(f'%{query}%')
        )

        # Then build individual word filters
        word_filters = [
            or_(
                Image.title.ilike(f'%{word}%'),
                Image.tag.ilike(f'%{word}%')
            ) for word in keywords
        ]

        results = Image.query.filter(or_(phrase_filter, *word_filters)).distinct().all()

        if not results:
            return render_template('404.html', query=query, auth=auth, current_user=current_user, user=user), 404  # Return a 404 page manually

        return render_template('index.html', images=results, query=query, current_user=current_user, auth=auth)

@phostel.route('/u/s/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    file = request.files.get('profile_picture')
    if not file or file.filename == '':
        return "No file selected", 400

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"

    # Manually specify the absolute path to the static folder
    upload_dir = os.path.join(os.getcwd(), 'static', 'u_profiles')  # Using os.getcwd() to get the project root
    os.makedirs(upload_dir, exist_ok=True)  # Ensure the folder exists

    # Save file using the absolute path
    save_path = os.path.join(upload_dir, unique_name)
    print("Saving to:", save_path)  # Debugging step to check where it saves

    file.save(save_path)

    # Store the relative path in DB
    current_user.picture = f"u_profiles/{unique_name}"
    db.session.commit()

    return redirect(url_for('phostel.user', user_id=current_user.id))

@phostel.route('/post', methods=['POST'])
@login_required
def post():
    if 'image' not in request.files:
        return "No file part", 400

    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400
    
    try:
        # Open the image using Pillow (without saving to disk first)
        img = PILImage.open(file)
        img.verify()  # Verify the image without loading it into memory

        # Re-open the image because 'verify()' doesn't load it into memory
        img = PILImage.open(file)
    except (IOError, SyntaxError) as e:
        return "File is not a valid image", 400

    title = request.form.get('title', '').strip()
    tag = request.form.get('tag', '').strip()

    # Sanitize and generate a unique filename
    ext = os.path.splitext(secure_filename(file.filename))[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    # Ensure upload folder exists
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_folder, unique_filename)
    img.save(file_path, format="JPEG", quality=80, optimize=True)

    # Save metadata to DB
    new_image = Image(
        id=str(uuid.uuid4()),
        filename=unique_filename,
        title=title,
        filepath=os.path.join("uploads", unique_filename),
        tag=tag,
        user=current_user
    )

    db.session.add(new_image)
    db.session.commit()

    return redirect(url_for('phostel.index'))

@phostel.route('/download/<image_id>')
def download(image_id):
    image = Image.query.get(str(image_id))
    if not image:
        abort(404)

    # Kemungkinan filenya ada di static uplod trus di download user yayayayaya
    upload_dir = os.path.join(os.getcwd(), 'static', 'uploads')
    return send_from_directory(upload_dir, image.filename, as_attachment=True)

@phostel.route('/tentang')
def about():
    return render_template('tentang.html')

@phostel.route('/like/<image_id>', methods=['POST'])
@login_required
def like(image_id):

    image = Image.query.get(str(image_id))
    if not image:
        abort(404)

    existing_like = Like.query.filter_by(user_id=current_user.id, image_id=image.id).first()

    if existing_like:
        db.session.delete(existing_like)
        # Optional: decrement like counter on Image
        image.like = (image.like or 1) - 1
    else:
        new_like = Like(user_id=current_user.id, image_id=image.id)
        db.session.add(new_like)
        # Optional: increment like counter on Image
        image.like = (image.like or 0) + 1

    db.session.commit()
    return redirect(request.referrer or url_for('phostel.index'))

@phostel.route('/del/<uuid:image_id>', methods=['POST'])
@login_required
def delete(image_id):
    image = Image.query.get(str(image_id))

    if not image:
        abort(404, description="Image not found")

    # Check if the current user owns the image
    if image.user_id != current_user.id:
        abort(403, description="You are not authorized to delete this image")

    # Optionally delete the image file from disk
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")

    # Delete from the database
    db.session.delete(image)
    db.session.commit()

    return redirect(url_for('phostel.index'))
