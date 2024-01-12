from flask import Flask
from flask_login import UserMixin, current_user, login_manager
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import os
import sqlite3
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from sqlalchemy import create_engine
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

# Making an isntance of the Flask Class (THis will get passed to app.py)
app = Flask(__name__,  template_folder='./templates')

bcrypt = Bcrypt(app)

# Adding cross site forgery protection
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
csrf = CSRFProtect(app)

# User authentication set up
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


# DataBase object configuration
class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)
    images = db.relationship('Image', backref='user', lazy=True)

    def get_all_image_links(self):
        return [image.image_link for image in self.images]

class Image(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_link = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"Image('{self.image_link}')"