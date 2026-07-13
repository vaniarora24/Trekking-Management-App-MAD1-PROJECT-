##Trekking Manegement App
## Developer: Vani Arora
## Description 
A Flask-based Trekking Management System where Admin, Staff, and Users can manage trekking activities.
It is a full-stack web application built with flask(Python) on the backend, SQLite for database management & HTML/CSS with Bootstrap for a responsive user-friendly responsive interface.

## Features

### Admin
- Pre-existing Superuser
- Add and Manage Treks
- Approve a newly registered Staff for first time login
- Deactivate or Blacklist Staff/ User
- Manage Users, Staffs and Treks
- Assign staff to treks
- View all the bookings
- Search trkes by their name, location or difficulty
- Keep report of Staff and Users
- Change password from settings 

### Staff
- Self- register & login after admin approval
- Get Assigned Treks by the Admin
- Update trek slots and status
- View and manage participant list
- Approve/Deny Participants
- Update Trek Status
- Edit Profile

### User
- Register and Login
- Browse Treks
- View Open Treks
- Search Trkes by their name, location or difficulty
- Book Treks
- View Booking Status and Trek Details
- View Booking History
- Edit Profile

## Technologies Used

- Python
- Flask
- SQLAlchemy
- SQLite
- Bootstrap
- HTML
- CSS
- Jinja2

## Run the Project

```bash
pip install -r requirements.txt
python app.py