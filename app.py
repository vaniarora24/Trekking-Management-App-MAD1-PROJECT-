from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

from dotenv import load_dotenv
import os
load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db= SQLAlchemy(app)

class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    is_admin = db.Column(db.Boolean , nullable=False, default=False)
    role = db.Column(db.String(10), nullable=False)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    blacklisted = db.Column(db.Boolean, default=False)
    date_of_creating_user = db.Column(db.DateTime, default=datetime.utcnow)

class Trek(db.Model):
    __tablename__="trekking"
    trek_id = db.Column(db.Integer, primary_key=True)
    trek_name= db.Column(db.String(32), unique=True)
    location= db.Column(db.String(60), nullable=False)
    difficulty= db.Column(db.String(10), nullable=False, default="moderate")
    duration_in_days= db.Column(db.Integer(), nullable=False)
    total_slots= db.Column(db.Integer())
    available_slots= db.Column(db.Integer())
    assigned_staff_id= db.Column(db.Integer(), db.ForeignKey('users.id'))
    status= db.Column(db.String(10), default="Open")
    start_date= db.Column(db.Date())
    end_date= db.Column(db.Date())


class Booking(db.Model):
    __tablename__="booking"
    booking_id= db.Column(db.Integer(), primary_key=True)
    user_id= db.Column(db.Integer(), db.ForeignKey('users.id'))
    trek_id= db.Column(db.Integer(), db.ForeignKey('trekking.trek_id'))
    booking_date= db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status= db.Column(db.String(10), default="booked")


class AssignedTreks(db.Model):
    __tablename__="assigned_treks"
    id= db.Column(db.Integer(), primary_key=True)
    staff_id= db.Column(db.Integer(), db.ForeignKey('users.id'))
    trek_id= db.Column(db.Integer(), db.ForeignKey('trekking.trek_id'))
    assigned_date= db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template("index.html", var1="VANI's")
    

@app.route('/login')
def login():
    return render_template('login.html', var1="VANI")

@app.route('/register')
def register():
    return render_template('register.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
    
    
