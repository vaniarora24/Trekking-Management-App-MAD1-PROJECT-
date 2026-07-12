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
    bookings = db.relationship("Booking", back_populates="user")

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
    staff = db.relationship("User", foreign_keys=[assigned_staff_id])
    status= db.Column(db.String(10), default="Open")
    start_date= db.Column(db.Date())
    end_date= db.Column(db.Date())
    bookings = db.relationship("Booking", back_populates="trek")

class Booking(db.Model):
    __tablename__="booking"
    booking_id= db.Column(db.Integer(), primary_key=True)
    user_id= db.Column(db.Integer(), db.ForeignKey('users.id'))
    trek_id= db.Column(db.Integer(), db.ForeignKey('trekking.trek_id'))
    booking_date= db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status= db.Column(db.String(10), default="booked")
    user = db.relationship("User", back_populates="bookings")
    trek = db.relationship("Trek", back_populates="bookings")

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
        if user.blacklisted == True:
            flash('Your account is rejected!')
            return redirect(url_for('login'))
        flash("Your account is awaiting admin approval")
        return redirect(url_for('login'))

    session['user_id'] = user.id
    flash('Login successful!')
    if user.is_admin:
        return redirect(url_for('admin'))
    elif user.role == 'Staff' and user.approved:
        return redirect(url_for('staff')) 
    elif user.role == 'User':
        return redirect(url_for('user'))
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
    flash('Registration successful!')
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
    recent_bookings= Booking.query.order_by(Booking.booking_date.desc()).limit(3).all()
    trek_count= Trek.query.count()
    user_count= User.query.filter_by(role='User').count()
    staff_count= User.query.filter_by(role='Staff').count()
    booking_count= Booking.query.count()
    return render_template('admin/dashboard.html', bookings=recent_bookings, trek_count=trek_count, user_count=user_count, staff_count=staff_count, booking_count=booking_count)

@app.route('/trek/manage')
@admin_required
def manage_trek():
    treks= Trek.query.all()
    search= request.args.get('search','')
    treks= Trek.query
    if search:
        treks= treks.filter(Trek.trek_name.ilike(f"%{search}%"))
    treks= treks.all()
    return render_template('admin/manage_trek.html', treks=treks, search= search)

@app.route('/search')
@admin_required
def search():
    search= request.args.get('search','')
    difficulty= request.args.get('difficulty','')
    location= request.args.get('location','')
    treks= Trek.query
    if search:
        treks= treks.filter(Trek.trek_name.ilike(f"%{search}%"))
    if difficulty:
        treks= treks.filter_by(difficulty=difficulty)
    if location:
        treks= treks.filter(Trek.location.ilike(f"%{location}%"))
    treks= treks.all()
    return render_template('admin/search.html', treks= treks, search= search, difficulty= difficulty)

@app.route('/trek/<int:trek_id>/edit')
@admin_required
def edit_trek(trek_id):
    trek= Trek.query.filter_by(trek_id=trek_id).first()
    staffs = User.query.filter_by(role="Staff", approved=True, blacklisted=False).all() #, approved=True
    return render_template('admin/edit_trek.html', trek=trek, staffs=staffs)

@app.route('/trek/<int:trek_id>/edit', methods=['POST'])
@admin_required
def edit_trek_post(trek_id):
    trek= Trek.query.filter_by(trek_id=trek_id).first()

    trekname = request.form.get('trekname')
    location =request.form.get('location')
    difficulty =request.form.get('difficulty')
    duration_in_days =int(request.form.get('duration_in_days'))
    available_slots =int(request.form.get('available_slots'))
    start_date =datetime.strptime(request.form.get('start_date'),"%Y-%m-%d").date()
    end_date =datetime.strptime(request.form.get('end_date'),"%Y-%m-%d").date()
    assigned_staff_id =int(request.form.get('assigned_staff_id'))
    status=request.form.get('status')
    if not trekname or not location or not status or not difficulty or not duration_in_days or not available_slots or not end_date or not assigned_staff_id:
        flash("Please fill out all the details")
        return redirect(url_for('edit_trek_post'))
    existing_trek= Trek.query.filter_by(trek_name=trekname, location=location, start_date=start_date, difficulty=difficulty, duration_in_days=duration_in_days, available_slots=available_slots, assigned_staff_id=assigned_staff_id, status=status).first()
    if existing_trek:
        flash('This trek already exists')
        return redirect(url_for('edit_trek', trek_id=trek_id))
    trek.trek_name= trekname
    trek.location= location
    trek.difficulty= difficulty
    trek.duration_in_days= duration_in_days
    trek.start_date= start_date
    trek.end_date= end_date
    trek.available_slots= available_slots
    trek.assigned_staff_id= assigned_staff_id
    trek.status= status
    bookings = Booking.query.filter_by(trek_id=trek.trek_id).all()
    for booking in bookings:
        booking.status = status
    db.session.commit()
    flash('Trek details edited successfully!')
    return redirect(url_for('manage_trek'))


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
    staffs= User.query.filter_by(role="Staff", approved=True, blacklisted=False).all()
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

@app.route('/staff/manage')
@admin_required
def manage_staff():
    status= request.args.get('status')
    if status == 'Pending':
        staffs= User.query.filter_by(role='Staff', approved=False, blacklisted=False).all()
    elif status == "Approved":
        staffs= User.query.filter_by(role='Staff', approved=True, blacklisted=False).all()
    elif status == "Blacklisted":
        staffs= User.query.filter_by(role='Staff', approved=False, blacklisted=True).all()
    else:
        staffs= User.query.filter_by(role='Staff').all()
    total_count= User.query.filter_by(role='Staff').count()
    pending_count= User.query.filter_by(role='Staff', approved=False, blacklisted=False).count()
    approved_count= User.query.filter_by(role='Staff', approved=True, blacklisted=False).count()
    blacklisted_count= User.query.filter_by(role='Staff', approved=False, blacklisted=True).count()
    return render_template('admin/manage_staff.html', staffs=staffs, pending_count=pending_count, approved_count=approved_count, blacklisted_count=blacklisted_count, total_count=total_count)
@app.route('/staff/<int:id>/approved')
def approved_staff(id):
    staff= User.query.get_or_404(id)
    staff.approved=True
    staff.blacklisted=False
    db.session.commit()
    flash('Staff approved successfully!')
    return redirect(url_for('manage_staff'))
@app.route('/staff/<int:id>/blacklisted')
def blacklisted_staff(id):
    staff= User.query.get_or_404(id)
    staff.approved=False
    staff.blacklisted=True
    db.session.commit()
    flash('Staff rejected!')
    return redirect(url_for('manage_staff'))

@app.route('/user/manage')
@admin_required
def manage_user():
    status= request.args.get('status')
    if status == 'Pending':
        users= User.query.filter_by(role='User', approved=False, blacklisted=False).all()
    elif status == "Approved":
        users= User.query.filter_by(role='User', approved=True, blacklisted=False).all()
    elif status == "Blacklisted":
        users= User.query.filter_by(role='User', approved=False, blacklisted=True).all()
    else:
        users= User.query.filter_by(role='User').all()
    total_count= User.query.filter_by(role='User').count()
    pending_count= User.query.filter_by(role='User', approved=False, blacklisted=False).count()
    approved_count= User.query.filter_by(role='User', approved=True, blacklisted=False).count()
    blacklisted_count= User.query.filter_by(role='User', approved=False, blacklisted=True).count()
    return render_template('admin/manage_user.html', users=users, total_count=total_count, pending_count=pending_count, approved_count=approved_count, blacklisted_count=blacklisted_count)
@app.route('/user/<int:id>/approved')
def approved_user(id):
    user= User.query.get_or_404(id)
    user.approved=True
    user.blacklisted=False
    db.session.commit()
    flash('User approved successfully!')
    return redirect(url_for('manage_user'))
@app.route('/user/<int:id>/blacklisted')
def blacklisted_user(id):
    user= User.query.get_or_404(id)
    user.approved=False
    user.blacklisted=True
    db.session.commit()
    flash('User rejected!')
    return redirect(url_for('manage_user'))

@app.route('/booking')
@admin_required
def booking():
    bookings= Booking.query.all()
    return render_template('admin/booking.html', bookings=bookings)

@app.route('/report')
@admin_required
def report():
    recent_bookings= Booking.query.order_by(Booking.booking_date.desc()).limit(3).all()
    trek_count= Trek.query.count()
    user_count= User.query.filter_by(role='User').count()
    staff_count= User.query.filter_by(role='Staff').count()
    booking_count= Booking.query.count()
    
    pending_count= User.query.filter_by(role='Staff', approved=False, blacklisted=False).count()
    approved_count= User.query.filter_by(role='Staff', approved=True, blacklisted=False).count()
    blacklisted_count= User.query.filter_by(role='Staff', approved=False, blacklisted=True).count()
    return render_template('admin/report.html', bookings=recent_bookings, trek_count=trek_count, user_count=user_count, staff_count=staff_count, booking_count=booking_count, pending_count=pending_count, approved_count=approved_count, blacklisted_count=blacklisted_count)

@app.route('/setting')
@admin_required
def setting():
    return render_template('admin/setting.html')

@app.route('/setting', methods=['POST'])
@admin_required
def setting_post():
    cpassword= request.form.get('cpassword')
    password= request.form.get('password')
    if not cpassword or not password:
        flash('Please fill all the details!')
        return redirect(url_for('setting'))
    admin= User.query.get(session['user_id'])
    if not check_password_hash(admin.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('setting'))
    new_password_hash= generate_password_hash(password)
    if cpassword == password:
        flash(' Current password and new password cannot be same!')
        return redirect(url_for('setting'))
    admin.passhash= new_password_hash
    flash('Password updated successfully!')
    return redirect(url_for('setting'))

@app.route('/staff')
@auth_required
def staff():
    staff_id= session['user_id']
    assigned_trek= Trek.query.filter_by(assigned_staff_id=staff_id).limit(3).all()
    assigned_trek_count= Trek.query.filter_by(assigned_staff_id=staff_id).count()
    participant_count= User.query.filter_by(role='User').count()
    open_trek_count= Trek.query.filter_by(assigned_staff_id=staff_id ,status='Open').count()
    return render_template('staff/staff_dashboard.html',treks=assigned_trek, assigned_trek=assigned_trek, assigned_trek_count=assigned_trek_count, participant_count=participant_count, open_trek_count=open_trek_count)

@app.route('/staff/staff_manage_trek')
@auth_required
def staff_manage_trek():
    staff_id= session['user_id']
    trek= Trek.query.filter_by(assigned_staff_id=staff_id).all()
    return render_template('staff/staff_manage_trek.html', treks=trek)

@app.route('/staff/staff_manage_trek/<int:trek_id>', methods=['GET', 'POST'])
@auth_required
def staff_trek_detail(trek_id):
    staff_id = session['user_id']
    trek = Trek.query.filter_by(trek_id=trek_id,assigned_staff_id=staff_id).first_or_404()
    if request.method=="POST":
        trek.available_slots= int(request.form['available_slots'])
        trek.status= request.form['status']
        bookings= Booking.query.filter_by(trek_id=trek_id).all()
        for booking in bookings:
            booking.status = trek.status
        db.session.commit()
        flash('Updated successfully!')
        return redirect(url_for('staff_trek_detail', trek_id= trek.trek_id))
    bookings= Booking.query.filter_by(trek_id=trek_id).all()
    return render_template('staff/staff_manage_trek.html',treks=[trek], bookings= bookings)

@app.route('/staff/trek/<int:trek_id>/start')
@auth_required
def mark_trek_started(trek_id):
    staff_id= session['user_id']
    trek= Trek.query.filter_by(trek_id= trek_id, assigned_staff_id= staff_id).first_or_404()
    trek.status = 'Started'
    bookings= Booking.query.filter_by(trek_id= trek_id).all()
    for booking in bookings:
        booking.status= 'Started'
    db.session.commit()
    flash('Trek successfully marked as started!')
    return redirect(url_for('staff_trek_detail', trek_id= trek_id))

@app.route('/staff/trek/<int:trek_id>/complete')
@auth_required
def mark_trek_completed(trek_id):
    staff_id= session['user_id']
    trek= Trek.query.filter_by(trek_id= trek_id, assigned_staff_id= staff_id).first_or_404()
    trek.status = 'Completed'
    bookings= Booking.query.filter_by(trek_id= trek_id).all()
    for booking in bookings:
        booking.status= 'Completed'
    db.session.commit()
    flash('Trek successfully marked as completed!')
    return redirect(url_for('staff_trek_detail', trek_id= trek_id))



@app.route('/staff/participants')
@auth_required
def participant():
    bookings= Booking.query.all()
    return render_template('staff/staff_manage_trek.html', bookings= bookings)

@app.route('/user')
@auth_required
def user():
    user= User.query.get(session['user_id'])
    treks= Trek.query.filter_by(status='Open').all()
    bookings= Booking.query.filter_by(user_id= session['user_id']).limit(3).all()
    return render_template("user/user_dashboard.html", user=user, treks=treks, bookings=bookings)

@app.route('/user_trek_detail/<int:trek_id>')
@auth_required
def user_trek_detail(trek_id):
    trek= Trek.query.get_or_404(trek_id)
    return render_template('user/user_trek_detail.html', trek=trek)

@app.route('/book_now/<int:trek_id>')
@auth_required
def book_now(trek_id):
    user_id= session['user_id']
    trek= Trek.query.get_or_404(trek_id)
    if trek.available_slots <=0:
        flash('No seats available!')
        return redirect(url_for('user'))
    existing_booking= Booking.query.filter_by(user_id=user_id, trek_id=trek_id).first()
    if existing_booking:
        flash('You have already booked this trek!')
        return redirect(url_for('user'))
    booking= Booking(user_id= user_id, trek_id= trek.trek_id, status= "Booked")
    db.session.add(booking)
    trek.available_slots -= 1
    db.session.commit()
    flash("Trek booked successfully!")
    return redirect(url_for('user'))

@app.route('/user/my_booking')
@auth_required
def my_booking():
    bookings= Booking.query.filter_by(user_id= session['user_id']).all()
    return render_template('user/my_booking.html', bookings=bookings)

@app.route('/user/booking_history')
@auth_required
def booking_history(): 
    bookings= Booking.query.filter_by(user_id= session['user_id'], status='Completed').all()
    return render_template('user/booking_history.html', bookings= bookings)

@app.route('/user/browse_trek')
@auth_required
def browse_trek():
    search= request.args.get('search','')
    difficulty= request.args.get('difficulty','')
    location= request.args.get('location','')
    treks= Trek.query
    if search:
        treks= treks.filter(Trek.trek_name.ilike(f"%{search}%"))
    if difficulty:
        treks= treks.filter_by(difficulty=difficulty)
    if location:
        treks= treks.filter(Trek.location.ilike(f"%{location}%"))
    treks= treks.all()
    return render_template('user/browse_trek.html', treks= treks, search= search, difficulty= difficulty)




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
    
    
