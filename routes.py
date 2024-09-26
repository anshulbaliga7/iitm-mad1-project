from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
from app import app
from models import db, User, Service, ServiceRequest
from werkzeug.security import generate_password_hash
from datetime import datetime

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
        # Handle the signup logic here
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        address = request.form['address']
        pincode = request.form['pincode']

        # Create a new user instance
        new_user = User(
            name=name,
            username=username,
            email=email,
            phone_number=phone_number,
            address=address,
            pincode=pincode,
            role='customer',  # Set role as customer
            blocked=False,  # Default value
            approval=None,  # Default value
            profile_photo=None  # Default value
        )
        
        # Set the password
        new_user.set_password(password)

        # Add the user to the session and commit
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Redirect to login or another page

    # If GET request, render the signup form
    return render_template('customer_signup.html')  # Ensure this template exists

@app.route('/service_professional_signup', methods=['GET', 'POST'])
def service_professional_signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']  # New field
        address = request.form['address']
        pincode = request.form['pincode']
        experience = request.form['experience']  # New field
        service_name = request.form['service_name']  # New field

        # Create a new user instance
        new_user = User(
        name=name,
        username=username,
        email=email,
        phone_number=phone_number,  # Include phone number
        address=address,
        pincode=pincode,
        experience=experience,  # Include experience
        service_name=service_name,  # Include service name
        role='service_professional',  # Set role as service professional
        blocked=False,  # Default value
        approval=None,  # Default value
        profile_photo=None  # Default value
        )

    # Set the password
        new_user.set_password(password)

    # Add the user to the session and commit
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('home'))  # Redirect to login or another page

    return render_template('service_professional_signup.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    services = Service.query.all()
    professionals = User.query.filter_by(role='service_professional').all()  # Fetch professionals
    service_requests = ServiceRequest.query.all()  # Fetch all service requests
    return render_template('admin_dashboard.html', services=services, professionals=professionals, service_requests=service_requests)

@app.route('/service_professional_dashboard')
def service_professional_dashboard():
    today = datetime.today().date()

    # Fetch today's active services (is_active = 1)
    today_services = ServiceRequest.query.join(Service).filter(
        Service.is_active == True,
        ServiceRequest.date_of_request >= today
    ).all()

    # Fetch closed services (is_active = 0)
    closed_services = ServiceRequest.query.join(Service).filter(
        Service.is_active == False,
        ServiceRequest.service_status == 'Closed'
    ).all()

    return render_template('service_professional_dashboard.html', today_services=today_services, closed_services=closed_services)

@app.route('/accept_service/<int:service_id>', methods=['POST'])
def accept_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if service_request:
        service_request.professional_id = session['user_id']  # Assign the professional
        service_request.service_status = 'Assigned'  # Update status
        db.session.commit()
        flash('Service request accepted successfully!', 'success')
    else:
        flash('Service request not found!', 'error')
    return redirect(url_for('service_professional_dashboard'))

@app.route('/reject_service/<int:service_id>', methods=['POST'])
def reject_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if service_request:
        db.session.delete(service_request)  # Remove the service request
        db.session.commit()
        flash('Service request rejected successfully!', 'success')
    else:
        flash('Service request not found!', 'error')
    return redirect(url_for('service_professional_dashboard'))

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
        phone_number = request.form['phone_number']
        address = request.form['address']
        pincode = request.form['pincode']
        
        # Check if the email or username already exists
        new_user = User(
        name=name,
        username=username,
        email=email,
        phone_number=phone_number,
        address=address,
        pincode=pincode,
        role='admin',  # Set role as admin
        blocked=False,  # Default value
        approval=None,  # Default value
        profile_photo=None  # Default value
        )
    
    # Set the password
        new_user.set_password(password)

    # Add the user to the session and commit
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('home'))  # Redirect to admin login page
    
    return render_template('admin_login.html')

@app.route('/admin/new_service', methods=['POST'])
def new_service():
    name = request.form['name']
    description = request.form['description']
    base_price = request.form['base_price']
    time_required = request.form['time_required']
    is_active = request.form['is_active'] == 'true'  # Convert to boolean
    category = request.form['category']  # Get the category from the form

    # Create a new service instance with all fields
    new_service = Service(
        name=name,
        description=description,
        price=base_price,
        time_required=time_required,
        is_active=is_active,
        category=category
    )

    # Add the new service to the session
    db.session.add(new_service)
    db.session.commit()  # Commit to save the service first

    # Now create a new service request for the newly created service
    # Assuming you have a customer_id available (you might need to get this from the form or session)
    customer_id = 2  # Get the customer ID from the form
    service_request = ServiceRequest(
        service_id=new_service.id,  # Use the ID of the newly created service
        customer_id=customer_id,
        professional_id=None,  # Set to None or the appropriate professional ID if applicable
        date_of_request=datetime.now(),  # Set the current date and time
        service_status='Requested',  # Initial status
        remarks=None,  # Optional remarks
        location=None,  # Optional location
        cost=None  # Optional cost, can be set later
    )

    # Add the new service request to the session
    db.session.add(service_request)
    db.session.commit()  # Commit to save the service request

    flash('New service and service request added successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_service/<int:service_id>', methods=['POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if service:
        service.name = request.form['name']
        service.description = request.form['description']
        service.price = request.form['base_price']
        service.time_required = request.form['time_required']
        service.is_active = request.form['is_active'] == 'true'  # Convert to boolean
        service.category = request.form['category']  # Update the category

        db.session.commit()
        flash('Service updated successfully!')
    else:
        flash('Service not found!', 'error')

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
    if professional:
        professional.approval = True  # Set approval to True
        professional.blocked = False   # Unblock the professional
        db.session.commit()
        flash('Professional approved successfully!', 'success')
    else:
        flash('Professional not found!', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_professional/<int:professional_id>', methods=['POST'])
def reject_professional(professional_id):
    professional = User.query.get(professional_id)
    if professional:
        professional.blocked = True    # Block the professional
        professional.approval = False   # Set approval to False
        db.session.commit()
        flash('Professional rejected successfully!', 'success')
    else:
        flash('Professional not found!', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_professional/<int:professional_id>', methods=['POST'])
def delete_professional(professional_id):
    professional = User.query.get(professional_id)
    if professional:
        db.session.delete(professional)  # Remove the professional from the User table
        db.session.commit()
        flash('Professional deleted successfully!', 'success')
    else:
        flash('Professional not found!', 'error')
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
            if search_text.lower() == 'active':
                results = Service.query.filter(Service.is_active == True).all()  # Fetch active services
            elif search_text.lower() == 'inactive':
                results = Service.query.filter(Service.is_active == False).all()  # Fetch inactive services
            else:
                results = Service.query.filter(Service.name.contains(search_text)).all()  # Fetch services by name

        elif search_type == 'customer':
            results = ServiceRequest.query.join(User).filter(User.name.contains(search_text)).all()

        elif search_type == 'professional':
            results = ServiceRequest.query.join(User).filter(User.name.contains(search_text)).all()

        elif search_type == 'service_request':
            if search_text.lower() == 'assigned':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Assigned').all()  # Fetch assigned service requests
            elif search_text.lower() == 'closed':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Closed').all()  # Fetch closed service requests
            else:
                results = ServiceRequest.query.filter(ServiceRequest.remarks.contains(search_text)).all()  # Fetch service requests by remarks

    return render_template('admin_search.html', results=results, search_type=search_type, search_text=search_text)

@app.route('/service_professional_search', methods=['GET', 'POST'])
def service_professional_search():
    results = []
    if request.method == 'POST':
        search_by = request.form['search_by']
        search_text = request.form['search_text']

        # Fetch service requests based on the search criteria
        if search_by == 'date':
            # Assuming search_text is in 'YYYY-MM-DD' format
            results = ServiceRequest.query.join(User, ServiceRequest.customer_id == User.id).filter(
                ServiceRequest.date_of_request == search_text
            ).all()
        elif search_by == 'location':
            results = ServiceRequest.query.join(User, ServiceRequest.customer_id == User.id).filter(
                ServiceRequest.location.contains(search_text)
            ).all()
        elif search_by == 'pincode':
            results = ServiceRequest.query.join(User, ServiceRequest.customer_id == User.id).filter(
                User.pincode == search_text
            ).all()

    return render_template('service_professional_search.html', results=results)