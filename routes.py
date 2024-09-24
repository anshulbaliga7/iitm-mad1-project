from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
from app import app
from models import db, User, Service, ServiceRequest
from werkzeug.security import generate_password_hash

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
        services = Service.query.all()
        professionals = User.query.filter_by(role='professional').all()
        service_requests = ServiceRequest.query.all()
        return render_template('admin_dashboard.html', services=services, professionals=professionals, service_requests=service_requests)
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

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if the email or username already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash('Email or username already registered. Please use a different email or username.')
            return redirect(url_for('admin_login'))
        
        # Create a new admin user with default values for non-relevant fields
        new_user = User(
            name=name,
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            address='N/A',  # Default value
            pincode=0,  # Default value
            experience=None,
            service_name=None,
            role='admin',
            documents=None
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Admin account created successfully. Please log in.')
        return redirect(url_for('home'))
    
    return render_template('admin_login.html')

@app.route('/admin/new_service', methods=['POST'])
def new_service():
    name = request.form['name']
    description = request.form['description']
    base_price = request.form['base_price']
    time_required = request.form['time_required']  # Add this line
    new_service = Service(name=name, description=description, price=base_price, time_required=time_required)  # Update this line
    db.session.add(new_service)
    db.session.commit()
    flash('New service added successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_service/<int:service_id>', methods=['POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    service.name = request.form['name']
    service.description = request.form['description']
    service.price = request.form['base_price']
    db.session.commit()
    flash('Service updated successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Service.query.get(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_professional/<int:professional_id>', methods=['POST'])
def approve_professional(professional_id):
    professional = User.query.get(professional_id)
    professional.approved = True
    db.session.commit()
    flash('Professional approved successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_professional/<int:professional_id>', methods=['POST'])
def reject_professional(professional_id):
    professional = User.query.get(professional_id)
    professional.approved = False
    db.session.commit()
    flash('Professional rejected successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_professional/<int:professional_id>', methods=['POST'])
def delete_professional(professional_id):
    professional = User.query.get(professional_id)
    db.session.delete(professional)
    db.session.commit()
    flash('Professional deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    results = []
    search_type = None
    search_text = None

    if request.method == 'POST':
        search_type = request.form['search_type']
        search_text = request.form['search_text']
        
        if search_type == 'service':
            results = ServiceRequest.query.join(Service).filter(Service.name.contains(search_text)).all()
        elif search_type == 'customer':
            results = ServiceRequest.query.join(User, ServiceRequest.customer_id == User.id).filter(User.name.contains(search_text)).all()
        elif search_type == 'professional':
            results = ServiceRequest.query.join(User, ServiceRequest.professional_id == User.id).filter(User.name.contains(search_text)).all()

    return render_template('admin_search.html', results=results, search_type=search_type, search_text=search_text)
    
    return render_template('admin_search.html')