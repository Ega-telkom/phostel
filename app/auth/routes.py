from flask import Flask, render_template, url_for, redirect, Response, Blueprint, request, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import subprocess
import uuid
import time
from functools import wraps
from datetime import datetime
import humanize
from app import db

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

login_manager = LoginManager()
login_manager.init_app(auth)
login_manager.login_view = "auth.signup"

def anonymous_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if current_user.is_authenticated:
            return render_template_string("""
            <!doctype html>
            <script>
              const ref = document.referrer;
              if (ref) location.href = ref;
              else history.back();
            </script>
            """)
        return view_func(*args, **kwargs)
    return wrapped_view

@login_manager.unauthorized_handler
def unauthorized():
    next_url = request.url[len(request.host_url):]
    return redirect(url_for('auth.signup', next=next_url))

class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    images = db.relationship('Image', back_populates='user')
    picture = db.Column(db.String(255), nullable=True)
    birth = db.Column(db.Integer, default=lambda: int(time.time()))
    admin = db.Column(db.Boolean, default=False)

    @property
    def is_admin(self):
        return self.admin == 1

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class Register(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=2, max=20)], render_kw={"class": "w-full item-center border border-solid border-abu-putih rounded-md p-2 text-sm"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=80)], render_kw={"class": "focus:outline-none focus:ring-0 w-full", "id": "password"})
    email = EmailField('Email', validators=[DataRequired(), Email()], render_kw={"class": "w-full item-center border border-solid border-abu-putih rounded-md p-2 text-sm"})
    submit = SubmitField("Lanjut", render_kw={"class": "active:bg-sky-900 hover:bg-sky-600 bg-biru-politik text-abu-indie p-2 rounded-md active:bg-sky-900 hover:bg-sky-900"})

class Login(FlaskForm):
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=80)], render_kw={"class": "focus:outline-none focus:ring-0 w-full", "id": "password"})
    email = EmailField('Email', validators=[DataRequired(), Email()], render_kw={"class": "w-full item-center border border-solid border-abu-putih rounded-md p-2 text-sm"})

    submit = SubmitField("Masuk", render_kw={"class": "active:bg-sky-900 hover:bg-sky-600 bg-biru-politik text-abu-indie p-2 rounded-md active:bg-sky-900 hover:bg-sky-900"})

@auth.route('/masuk', methods=['GET', 'POST'])
@anonymous_required
def login():
    form = Login()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=True) # MASUK!
                return redirect(url_for('phostel.index'))
            else:
                return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('auth.login'))

    return render_template('login.html', form=form)

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(request.referrer or url_for('phostel.index'))

@auth.route('/daftar', methods=['GET', 'POST'])
@anonymous_required
def signup():
    form = Register()

    next_page = request.args.get('next')

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email sudah ada yang memakai!", "email")
            return redirect(url_for('auth.signup'))  # or some error page
        else:
            hash_brown = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_user = User(
                username=form.username.data,
                password=hash_brown,
                email=form.email.data
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)  # <- login the *new* user
            return redirect(next_page or url_for('phostel.index'))

    return render_template('signup.html', form=form)

@auth.route('/admin')
def dump_user_table():
    try:
        # Run sqlite3 and execute commands
        output = subprocess.check_output([
            'sqlite3', 'instance/data.db',
            '-cmd', '.mode box',
            'SELECT * FROM user;'
            'SELECT * FROM image;'
            'SELECT * FROM like;'
        ])
        return Response(output, mimetype='text/plain')
    except subprocess.CalledProcessError:
        return Response("Failed to query database.", status=500, mimetype='text/plain')