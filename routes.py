from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
from app import app
from models import db, User

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(email=email, username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'service_professional':
                return redirect(url_for('service_professional_dashboard'))
            elif user.role == 'customer':
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        pincode = request.form['pincode']
        
        new_user = User(name=name, username=username, email=email, address=address, pincode=pincode, role='customer')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Customer registered successfully. Please login.')
        return redirect(url_for('home'))
    
    return render_template('customer_signup.html')

@app.route('/service_professional_signup', methods=['GET', 'POST'])
def service_professional_signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        pincode = request.form['pincode']
        experience = request.form['experience']
        service_name = request.form['service_name']
        
        documents_path = None  # Initialize documents_path
        
        if 'documents' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['documents']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            documents_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if documents_path:  # Ensure documents_path is valid
            new_user = User(name=name, username=username, email=email, address=address, pincode=pincode, experience=experience, service_name=service_name, role='service_professional', documents=documents_path)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Service Professional registered successfully. Please login.')
            return redirect(url_for('home'))
        else:
            flash('Failed to upload documents. Please try again.')
            return redirect(request.url)
    
    return render_template('service_professional_signup.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    return redirect(url_for('home'))

@app.route('/service_professional_dashboard')
def service_professional_dashboard():
    if 'user_id' in session and session['role'] == 'service_professional':
        return render_template('service_professional_dashboard.html')
    return redirect(url_for('home'))

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user_id' in session and session['role'] == 'customer':
        return render_template('customer_dashboard.html')
    return redirect(url_for('home'))