from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

import enum

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    experience = db.Column(db.Integer, nullable=True)  # Only for service professionals
    service_name = db.Column(db.String(80), nullable=True)  # Only for service professionals
    role = db.Column(db.String(20), nullable=False)
    documents = db.Column(db.String(200), nullable=True)  # Only for service professionals
    blocked = db.Column(db.Boolean, default=False)
    approval = db.Column(db.Boolean, nullable=True)  # Only for service professionals
    profile_photo = db.Column(db.String(200), nullable=True)  
    rating = db.Column(db.Integer, nullable=True, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True) 
    category = db.Column(db.String(80), nullable=True)  


class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, nullable=False)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    service_status = db.Column(db.String(20), nullable=False)  # Requested, Assigned, Closed
    remarks = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True) 
    cost = db.Column(db.Float, nullable=True) 

    service = db.relationship('Service', backref=db.backref('requests', lazy=True))
    customer = db.relationship('User', foreign_keys=[customer_id], backref=db.backref('customer_requests', lazy=True))
    professional = db.relationship('User', foreign_keys=[professional_id], backref=db.backref('professional_requests', lazy=True))

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), nullable=False)
