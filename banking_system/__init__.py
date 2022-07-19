from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ
import os
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.secret_key = environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/banking_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SALT'] = environ.get('SALT')
db = SQLAlchemy(app)

from banking_system import model
from banking_system import routes