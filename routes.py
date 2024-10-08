from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
from app import app
from models import db, User, Service, ServiceRequest
from werkzeug.security import generate_password_hash
from datetime import datetime
from sqlalchemy import func

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/service_professional_blocked')
def service_professional_blocked():
    return render_template('service_professional_blocked.html')

@app.route('/customer_blocked')
def customer_blocked():
    return render_template('customer_blocked.html')  # Render the blocked page template

@app.route('/any_page_noaccess')
def any_page_noaccess():
    return render_template('any_page_noaccess.html')  # Render the blocked page template

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
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the session
    session.pop('user_id', None)  # Remove user_id from session
    flash('You have been logged out.', 'success')  # Optional: flash a message
    return redirect(url_for('home'))  # Redirect to the login page

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
    services = Service.query.all()  # Fetch all services

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        address = request.form['address']
        pincode = request.form['pincode']
        experience = request.form['experience']
        service_name = request.form['service_name']

        # Create a new user instance
        new_user = User(
            name=name,
            username=username,
            email=email,
            phone_number=phone_number,
            address=address,
            pincode=pincode,
            experience=experience,
            service_name=service_name,
            role='service_professional',
            blocked=False,
            approval=None,
            profile_photo=None
        )

        # Set the password
        new_user.set_password(password)

        # Add the user to the session and commit
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('home'))

    return render_template('service_professional_signup.html', services=services)  # Pass services to the template

@app.route('/admin_dashboard')
def admin_dashboard():
    services = Service.query.all()
    professionals = User.query.filter_by(role='service_professional').all()  # Fetch professionals
    customers = User.query.filter_by(role='customer').all()
    service_requests = ServiceRequest.query.all()  # Fetch all service requests
    return render_template('admin_dashboard.html', services=services, professionals=professionals, customers=customers, service_requests=service_requests)

@app.route('/admin/block_customer/<int:customer_id>', methods=['POST'])
def block_customer(customer_id):
    customer = User.query.get(customer_id)  # Assuming you have a Customer model
    if customer:
        customer.blocked = 1  # Set blocked status
        customer.approval = 0  # Set approval status
        db.session.commit()  # Commit the changes
    return redirect(url_for('admin_search'))  # Redirect back to the search page

@app.route('/admin/unblock_customer/<int:customer_id>', methods=['POST'])
def unblock_customer(customer_id):
    customer = User.query.get(customer_id)  # Assuming you have a User model
    if customer:
        customer.blocked = 0  # Set blocked status to 0 (unblocked)
        db.session.commit()  # Commit the changes
    return redirect(url_for('admin_search'))  # Redirect back to the search page

@app.route('/admin/block_customer1/<int:customer_id>', methods=['POST'])
def block_customer1(customer_id):
    customer = User.query.get(customer_id)  # Assuming you have a Customer model
    if customer:
        customer.blocked = 1  # Set blocked status
        customer.approval = 0  # Set approval status
        db.session.commit()  # Commit the changes
    return redirect(url_for('admin_dashboard'))  # Redirect back to the search page

@app.route('/admin/unblock_customer1/<int:customer_id>', methods=['POST'])
def unblock_customer1(customer_id):
    customer = User.query.get(customer_id)  # Assuming you have a User model
    if customer:
        customer.blocked = 0  # Set blocked status to 0 (unblocked)
        db.session.commit()  # Commit the changes
    return redirect(url_for('admin_dashboard'))  # Redirect back to the search page

@app.route('/admin/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer = User.query.get(customer_id)
    if customer:
        db.session.delete(customer)  # Remove the professional from the User table
        db.session.commit()
    else:
        flash('Professional not found!', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/accept_professional/<int:professional_id>', methods=['POST'])
def accept_professional(professional_id):
    professional = User.query.get(professional_id)  # Assuming you have a User model
    if professional:
        professional.approval = True  # Set approval status to accepted
        professional.blocked = False
        db.session.commit()  # Commit the changes
    return redirect(url_for('admin_search'))  # Redirect back to the search page

@app.route('/admin/block_professional/<int:professional_id>', methods=['POST'])
def block_professional(professional_id):
    professional = User.query.get(professional_id)  # Assuming you have a User model
    if professional:
        professional.blocked = True  # Set blocked status
        professional.approval = False
        db.session.commit()  # Commit the changes
    return redirect(url_for('admin_search'))  # Redirect back to the search page

@app.route('/edit_service_request/<int:request_id>', methods=['POST'])
def edit_service_request(request_id):
    request_to_edit = ServiceRequest.query.get(request_id)  # Assuming you have a ServiceRequest model
    if request_to_edit:
        # Convert the date string to a datetime object
        date_of_request_str = request.form['requested_date']
        request_to_edit.date_of_request = datetime.strptime(date_of_request_str, '%Y-%m-%d').date()  # Adjust format if necessary
        request_to_edit.remarks = request.form['remarks']
        db.session.commit()  # Commit the changes
    return redirect(url_for('customer_dashboard'))  # Redirect back to the customer dashboard

@app.route('/service_professional_dashboard')
def service_professional_dashboard():
    today = datetime.today().date()
    current_professional_id = session.get('user_id')

    # Fetch the professional's details
    professional = User.query.filter_by(id=current_professional_id, role='service_professional').first()
    if not current_professional_id:
        return redirect(url_for('any_page_noaccess'))
    # Check if the professional is approved and not blocked
    #add this once done:  and professional.approval == 1 and professional.blocked == 0
    if professional and professional.approval == 1 and professional.blocked == 0:
        # Fetch today's active services (is_active = 1) that match the professional's service_name
        today_services = ServiceRequest.query.join(Service).filter(
            Service.is_active == True,
            ServiceRequest.service_status != 'Closed',
            Service.name == professional.service_name  # Filter by the professional's service_name
        ).all()

        # Fetch closed services (is_active = 0) that match the professional's service_name
        closed_services = ServiceRequest.query.join(Service).filter(
            ServiceRequest.service_status == 'Closed',
            Service.name == professional.service_name  # Filter by the professional's service_name
        ).all()

        return render_template('service_professional_dashboard.html', today_services=today_services, closed_services=closed_services, professional=professional)
    else:
        flash('Access denied: Your account is either blocked or not approved.', 'error')
        return redirect(url_for('service_professional_blocked'))  # Redirect to home or another appropriate page

@app.route('/update_profile', methods=['POST'])
def update_profile():
    # Assuming you have a way to get the current professional's ID
    current_professional_id = session.get('user_id')

    # Fetch the professional's details
    professional = User.query.get(current_professional_id)

    # Update the professional's details
    professional.name = request.form['name']
    professional.email = request.form['email']
    professional.phone_number = request.form['phone_number']
    professional.address = request.form['address']
    professional.pincode = request.form['pincode']
    professional.experience = request.form['experience']
    professional.service_name = request.form['service_name']

    # Commit the changes to the database
    db.session.commit()

    # Redirect back to the dashboard or show a success message
    return redirect(url_for('service_professional_dashboard'))

@app.route('/update_profile_customer', methods=['POST'])
def update_profile_customer():
    # Assuming you have a way to get the current professional's ID
    current_customer_id = session.get('user_id')

    # Fetch the professional's details
    customer = User.query.get(current_customer_id)

    # Update the professional's details
    customer.name = request.form['name']
    customer.email = request.form['email']
    customer.phone_number = request.form['phone_number']
    customer.address = request.form['address']
    customer.pincode = request.form['pincode']

    # Commit the changes to the database
    db.session.commit()

    # Redirect back to the dashboard or show a success message
    return redirect(url_for('customer_dashboard'))

@app.route('/accept_service/<int:service_id>', methods=['POST'])
def accept_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if service_request:
        service_request.professional_id = session.get('user_id')
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
    user_id = session.get('user_id')
    user = User.query.get(user_id)  # Query the User table for the user
    if not user_id:
        return redirect(url_for('any_page_noaccess'))
    # Check if the user is blocked
    if user and user.blocked == 1:
        return redirect(url_for('customer_blocked'))  # Redirect to the blocked page

    customer = User.query.filter_by(id=user_id, role='customer').first()
    
    # Fetch all available services
    services = Service.query.filter_by(is_active=True).all()  # Assuming you want only active services

    # Fetch service history for the customer
    service_history = ServiceRequest.query \
        .join(Service, ServiceRequest.service_id == Service.id) \
        .join(User, ServiceRequest.customer_id == User.id) \
        .filter(ServiceRequest.customer_id == user_id) \
        .all()

    return render_template('customer_dashboard.html', customer=customer, services=services, service_history=service_history, user=user)

@app.route('/book_service', methods=['POST'])
def book_service():
    service_id = request.form['service_id']
    date_of_request_str = request.form['date_of_request']
    remarks = request.form['remarks']
    
    # Convert the date string to a datetime object
    date_of_request = datetime.strptime(date_of_request_str, '%Y-%m-%d').date()  # Adjust format if necessary

    # Assuming you have a way to get the current customer's ID
    customer_id = session.get('user_id')
    service = Service.query.filter_by(id=service_id).first()
    service_price = service.price
    # Create a new service request
    new_request = ServiceRequest(
        service_id=service_id,
        customer_id=customer_id,
        professional_id=None,  # Set to None as per your requirement
        service_status='Requested',
        date_of_request=date_of_request,
        remarks=remarks,
        cost=service_price
    )

    # Add to the session and commit to the database
    db.session.add(new_request)
    db.session.commit()

    # Redirect back to the customer dashboard or show a success message
    return redirect(url_for('customer_dashboard'))

@app.route('/book_service1', methods=['POST'])
def book_service1():
    service_id = request.form['service_id']
    date_of_request_str = request.form['date_of_request']
    remarks = request.form['remarks']
    
    # Convert the date string to a datetime object
    date_of_request = datetime.strptime(date_of_request_str, '%Y-%m-%d').date()  # Adjust format if necessary

    # Assuming you have a way to get the current customer's ID
    customer_id = session.get('user_id')

    # Create a new service request
    new_request = ServiceRequest(
        service_id=service_id,
        customer_id=customer_id,
        professional_id=None,  # Set to None as per your requirement
        service_status='Requested',
        date_of_request=date_of_request,
        remarks=remarks
    )

    # Add to the session and commit to the database
    db.session.add(new_request)
    db.session.commit()

    # Redirect back to the customer dashboard or show a success message
    return redirect(url_for('customer_dashboard'))

@app.route('/customer_search', methods=['GET', 'POST'])
def customer_search():
    # Logic to handle the search
    user_id = session.get('user_id')

    # Fetch unique service names for the dropdown
    unique_services = Service.query.distinct(Service.name).all()

    # Fetch service history for the logged-in user
    service_history = ServiceRequest.query \
        .join(Service, ServiceRequest.service_id == Service.id) \
        .join(User, ServiceRequest.customer_id == User.id) \
        .filter(ServiceRequest.customer_id == user_id) \
        .all()

    return render_template('customer_search.html', services=unique_services, service_history=service_history)

@app.route('/search_services', methods=['POST'])
def search_services():
    service_name = request.form.get('service_name')
    search_text = request.form.get('search_text')
    
    # Initialize the query
    user_id = 2  # Replace with actual user ID from session or context
    query = Service.query

    # If a service name is provided, filter by that service name
    if service_name:
        query = query.filter(Service.name == service_name)

    # If search text is provided, filter by description
    if search_text:
        query = query.filter(Service.description.contains(search_text))

    # Execute the query
    search_results = query.all()

    # Fetch service history
    service_history = ServiceRequest.query \
        .join(Service, ServiceRequest.service_id == Service.id) \
        .join(User, ServiceRequest.customer_id == User.id) \
        .filter(ServiceRequest.customer_id == user_id) \
        .all()

    # Get unique service names for the dropdown
    unique_services = Service.query.distinct(Service.name).all()

    return render_template('customer_search.html', services=unique_services, search_results=search_results, search_text=search_text, service_history=service_history)

@app.route('/close_service_request/<int:request_id>', methods=['POST'])
def close_service_request(request_id):
    # Fetch the service request from the database
    request_to_close = ServiceRequest.query.get(request_id)
    if request_to_close:
        request_to_close.service_status = 'Closed'  # Update the status
        request_to_close.remarks = request.form.get('remarks', '')  # Capture remarks
        db.session.commit()  # Commit the changes
        flash('Service request closed successfully!', 'success')
    else:
        flash('Service request not found!', 'error')

    return redirect(url_for('customer_dashboard'))  # Redirect back to the dashboard

@app.route('/close_service1/<int:service_id>', methods=['POST'])
def close_service1(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if service_request and service_request.service_status == 'Assigned':
        service_request.service_status = 'Closed'  # Update status to Closed
        service_request.date_of_completion = datetime.now()  # Record the completion date
        db.session.commit()  # Commit the changes
        flash('Service request closed successfully!', 'success')
    else:
        flash('Service request not found or cannot be closed.', 'danger')

    return redirect(url_for('service_professional_dashboard'))  # Redirect back to the dashboard

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
    # customer_id = 2  # Get the customer ID from the form
    # service_request = ServiceRequest(
    #     service_id=new_service.id,  # Use the ID of the newly created service
    #     customer_id=customer_id,
    #     professional_id=None,  # Set to None or the appropriate professional ID if applicable
    #     date_of_request=datetime.now(),  # Set the current date and time
    #     service_status='Requested',  # Initial status
    #     remarks=None,  # Optional remarks
    #     location=None,  # Optional location
    #     cost=None  # Optional cost, can be set later
    # )

    # Add the new service request to the session
    # db.session.add(service_request)
    # db.session.commit()  # Commit to save the service request

    # flash('New service and service request added successfully!')
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
            results = User.query.filter(User.name.contains(search_text), User.role == 'customer').all()

        elif search_type == 'professional':
            results = User.query.filter(User.name.contains(search_text), User.role == 'service_professional').all()

        elif search_type == 'service_request':
            if search_text.lower() == 'assigned':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Assigned').all()  # Fetch assigned service requests
            elif search_text.lower() == 'closed':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Closed').all()  # Fetch closed service requests
            elif search_text.lower() == 'requested':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Requested').all()  # Fetch closed service requests
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
                func.date(ServiceRequest.date_of_request) == search_text  # Extract date part for comparison
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

@app.route('/admin_summary')
def admin_summary():
    # Fetch service requests data
    service_requests = ServiceRequest.query.all()

    # Prepare data for charts
    service_counts = {}
    completion_counts = {'Requested': 0, 'Assigned': 0, 'Closed': 0}
    revenue_data = {}

    for request in service_requests:
        # Count service statuses
        if request.service_status in completion_counts:
            completion_counts[request.service_status] += 1

        # Calculate total revenue per service
        service_name = request.service.name
        if request.cost is not None:  # Check if cost is not None
            revenue_data[service_name] = revenue_data.get(service_name, 0) + request.cost

    # Fetch services data
    services = Service.query.all()
    for service in services:
        service_name = service.name
        service_counts[service_name] = service_counts.get(service_name, 0) + 1

    return render_template('admin_summary.html', 
                           service_counts=service_counts, 
                           completion_counts=completion_counts, 
                           revenue_data=revenue_data)  # Pass revenue data to the template

@app.route('/service_professional_summary')
def service_professional_summary():
    # Get the logged-in professional's ID
    professional_id = session.get('user_id')

    # Fetch service requests assigned to this professional
    service_requests = ServiceRequest.query.filter_by(professional_id=professional_id).all()

    # Prepare data for charts
    completion_counts = {'Requested': 0, 'Assigned': 0, 'Closed': 0}
    customer_request_counts = {}

    for request in service_requests:
        # Count service statuses
        if request.service_status in completion_counts:
            completion_counts[request.service_status] += 1

        # Get the customer's name by fetching from the User table based on customer_id
        customer = User.query.filter_by(id=request.customer_id).first()
        customer_name = customer.name if customer else 'Unknown'

        # Count the number of requests per customer for this service
        if customer_name not in customer_request_counts:
            customer_request_counts[customer_name] = 0
        customer_request_counts[customer_name] += 1

    # Fetch the single service for the logged-in professional
    service_name = service_requests[0].service.name if service_requests else 'No service assigned'

    return render_template('service_professional_summary.html', 
                           service_name=service_name,
                           customer_request_counts=customer_request_counts, 
                           completion_counts=completion_counts)


@app.route('/customer_summary')
def customer_summary():
    # Assuming you have a way to get the current customer's ID from the session
    customer_id = session.get('user_id')
    
    if not customer_id:
        # Handle the case where the customer is not logged in or session expired
        flash('Please log in to view your summary.', 'error')
        return redirect(url_for('login'))

    # Fetch service requests data for the current customer only
    service_requests = ServiceRequest.query.filter_by(customer_id=customer_id).all()

    # Prepare data for charts
    service_counts = {}
    completion_counts = {'Requested': 0, 'Assigned': 0, 'Closed': 0}
    revenue_data = {}  # Dictionary to track revenue for each service

    for request in service_requests:
        # Count service statuses for the logged-in customer
        if request.service_status in completion_counts:
            completion_counts[request.service_status] += 1

        # Fetch the service name for each service request
        service_name = request.service.name  # Assuming there is a relationship between ServiceRequest and Service

        # Count how many times each service was requested
        service_counts[service_name] = service_counts.get(service_name, 0) + 1

        # Add the cost to revenue data if it's not None
        if request.cost is not None:
            revenue_data[service_name] = revenue_data.get(service_name, 0) + request.cost

    return render_template('customer_summary.html', 
                           service_counts=service_counts, 
                           completion_counts=completion_counts,
                           revenue_data=revenue_data)

