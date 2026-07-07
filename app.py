from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import  generate_password_hash,check_password_hash
from functools import wraps

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
    trek_name= db.Column(db.String(32), nullable=False)
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

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('You are not logged in to the page!')
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('You are not logged in to the page!')
            return redirect(url_for('login'))
        user= User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You are not authorized to access this page!')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

@app.route('/')
@auth_required
def index():
    user= User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    return render_template("index.html", var1="VANI's")

@app.route('/login')
def login():
    return render_template('login.html', var1="VANI")

@app.route('/login', methods=['POST'])
def login_post():
    email=request.form.get('email')
    password= request.form.get('password')
    if not email or not password:
        flash('Please fill out all the details')
        return redirect(url_for('login'))
    user= User.query.filter_by(email=email).first()
    if not user:
        flash("User doesnot exists")
        return redirect(url_for('login'))
    if not check_password_hash(user.passhash, password):
        flash('Invalid password')
        return redirect(url_for('login'))
    if user.role == "Staff" and not user.approved:
        flash("Your account is awaiting admin approval.")
        return redirect(url_for('login'))

    session['user_id'] = user.id
    flash('Login Successful!')
    return redirect(url_for('index'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    fullname= request.form.get('fullname')
    email= request.form.get('email')
    password= request.form.get('password')
    confirm_password= request.form.get('confirm_password')
    contact = request.form.get('contact')
    role = request.form.get('role')
    
    if not fullname or not email or not password or not confirm_password or not role:
        flash('Please fill out all the details')
        return redirect(url_for('register'))
    if password != confirm_password:
        flash("Password donot match")
        return redirect(url_for('register'))
    user= User.query.filter_by(email=email).first()

    if user:
        flash('User with this email already exists')
        return redirect(url_for('register'))
    
    password_hash= generate_password_hash(password)
    new_user= User(username=email, email=email, passhash=password_hash, name=fullname, contact=contact, role=role)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/profile')
@auth_required
def profile():
    user= User.query.get(session['user_id'])
    return render_template("profile.html", user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def edit_profile():
    username= request.form.get('username')
    cpassword= request.form.get('cpassword')
    password= request.form.get('password')
    name= request.form.get('name')
    email= request.form.get('email')

    if not username or not cpassword or not password or not name or not email:
        flash('Please fill all the details!')
        return redirect(url_for('profile'))
    
    user= User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))
    
    if username != user.username:
        new_username= User.query.filter_by(username=username).first()
        if new_username:
            flash('User already exists!')
            return redirect(url_for('profile'))
    if email != user.email:
        new_email= User.query.filter_by(email=email).first()
        if new_email:
            flash('User already exists!')
            return redirect(url_for('profile'))
        
    new_password_hash= generate_password_hash(password)
    user.username= username
    user.email= email
    user.passhash= new_password_hash
    user.name= name
    db.session.commit()
    flash('Profile updated successfully!')
    return redirect(url_for('profile'))

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin/dashboard.html')

@app.route('/trek/manage')
@admin_required
def manage_trek():
    treks= Trek.query.all()
    return render_template('admin/manage_trek.html', treks=treks)

@app.route('/trek/<int:trek_id>/edit')
@admin_required
def edit_trek(trek_id):
    return render_template('admin/edit_trek.html')

@app.route('/trek/<int:trek_id>/delete')
@admin_required
def delete_trek(trek_id):
    trek= Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted successfully!')
    return redirect(url_for('manage_trek'))

@app.route('/trek/add')
@admin_required
def add_trek():
    staffs= User.query.filter_by(role="Staff").all()
    return render_template('admin/add_trek.html', staffs=staffs)
@app.route('/trek/add', methods=['POST'])
@admin_required
def add_trek_post():
    trekname = request.form.get('trekname')
    location =request.form.get('location')
    difficulty =request.form.get('difficulty')
    duration_in_days =int(request.form.get('duration_in_days'))
    available_slots =int(request.form.get('available_slots'))
    start_date =datetime.strptime(request.form.get('start_date'),"%Y-%m-%d").date()
    end_date =datetime.strptime(request.form.get('end_date'),"%Y-%m-%d").date()
    assigned_staff_id =int(request.form.get('assigned_staff_id'))
    status=request.form.get('status')
    if not trekname or not location or not status:
        flash("Please fill out all the details")
        return redirect(url_for('add_trek_post'))
    
    existing_trek= Trek.query.filter_by(trek_name=trekname, start_date=start_date).first()
    if existing_trek:
        flash('This trek already_exists')
        return redirect(url_for('add_trek'))
    new_trek= Trek(trek_name=trekname, location=location, difficulty=difficulty, duration_in_days=duration_in_days, available_slots=available_slots, total_slots=available_slots, start_date=start_date, end_date=end_date, assigned_staff_id=assigned_staff_id, status=status)
    db.session.add(new_trek)
    db.session.commit()
    flash('Trek added successfully!')
    return redirect(url_for('manage_trek'))

@app.route('/booking')
@admin_required
def booking():
    return render_template('admin/dashboard.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        admin= User.query.filter_by(is_admin=True).first()
        if not admin:
            password_hash= generate_password_hash('admin')
            admin= User(username='admin@gmail.com', email='admin@gmail.com',passhash=password_hash, name='Admin', contact='9876543210', role='Admin', approved=True, is_admin=True)
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
    
    
