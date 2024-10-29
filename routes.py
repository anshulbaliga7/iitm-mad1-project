from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename, safe_join
import os
from app import app
from models import db, User, Service, ServiceRequest, Log
from werkzeug.security import generate_password_hash
from datetime import datetime
from sqlalchemy import func

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/service_professional_blocked')
def service_professional_blocked():
    return render_template('service_professional_blocked.html')

@app.route('/admin_logs')
def admin_logs():
    logs = Log.query.all()  
    return render_template('admin_logs.html', logs=logs)

@app.route('/customer_blocked')
def customer_blocked():
    return render_template('customer_blocked.html') 

@app.route('/any_page_noaccess')
def any_page_noaccess():
    return render_template('any_page_noaccess.html')  

@app.route('/download/<filename>')
def download_document(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


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
            
            log_entry = Log(
                timestamp=datetime.now(),  
                action="User logged in successfully", 
                username=username  
            )
            db.session.add(log_entry)  
            db.session.commit() 

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'service_professional':
                return redirect(url_for('service_professional_dashboard'))
            elif user.role == 'customer':
                return redirect(url_for('customer_dashboard'))
        else:
            log_entry = Log(
                timestamp=datetime.now(),  
                action="User denied access for incorrect username/password", 
                username=username 
            )
            db.session.add(log_entry)  
            db.session.commit()  
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  
    return redirect(url_for('home')) 

@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        address = request.form['address']
        pincode = request.form['pincode']

        new_user = User(
            name=name,
            username=username,
            email=email,
            phone_number=phone_number,
            address=address,
            pincode=pincode,
            role='customer', 
            blocked=False,  
            approval=None,  
            profile_photo=None 
        )
        
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  

    return render_template('customer_signup.html')  

@app.route('/service_professional_signup', methods=['GET', 'POST'])
def service_professional_signup():
    services = Service.query.all()

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

        file = request.files.get('documents')
        
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            file.save(filepath)
            
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
                profile_photo=None,
                documents=filepath  
            )

            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            log_entry = Log(
                timestamp=datetime.now(),
                action="Professional signed up successfully",
                username=username
            )
            db.session.add(log_entry)
            db.session.commit()

            return redirect(url_for('home'))
        
        else:
            return "File not provided", 400

    return render_template('service_professional_signup.html', services=services)

@app.route('/admin_dashboard')
def admin_dashboard():
    services = Service.query.all()
    professionals = User.query.filter_by(role='service_professional').all()
    customers = User.query.filter_by(role='customer').all()
    service_requests = ServiceRequest.query.all()

    for professional in professionals:
        if professional.documents:
            professional.document_filename = os.path.basename(professional.documents)
        else:
            professional.document_filename = None

    return render_template(
        'admin_dashboard.html',
        services=services,
        professionals=professionals,
        customers=customers,
        service_requests=service_requests
    )

@app.route('/admin/block_customer/<int:customer_id>', methods=['POST'])
def block_customer(customer_id):
    customer = User.query.get(customer_id) 
    if customer:
        customer.blocked = 1  
        customer.approval = 0 
        db.session.commit() 

        log_entry = Log(
            timestamp=datetime.now(),  
            action=f"Customer '{customer.username}' blocked",  
            username='admin'  
        )
        db.session.add(log_entry) 
        db.session.commit() 
    return redirect(url_for('admin_search'))  

@app.route('/admin/unblock_customer/<int:customer_id>', methods=['POST'])
def unblock_customer(customer_id):
    customer = User.query.get(customer_id)  
    if customer:
        customer.blocked = 0 
        db.session.commit() 

        log_entry = Log(
            timestamp=datetime.now(),  
            action=f"Customer '{customer.username}' unblocked", 
            username='admin'  
        )
        db.session.add(log_entry)  
        db.session.commit()  
    return redirect(url_for('admin_search'))  

@app.route('/admin/block_customer1/<int:customer_id>', methods=['POST'])
def block_customer1(customer_id):
    customer = User.query.get(customer_id) 
    if customer:
        customer.blocked = 1 
        customer.approval = 0  
        db.session.commit() 

        log_entry = Log(
            timestamp=datetime.now(),  
            action=f"Customer '{customer.username}' blocked",  
            username='admin'  
        )
        db.session.add(log_entry)  
        db.session.commit()  
    return redirect(url_for('admin_dashboard'))  

@app.route('/admin/unblock_customer1/<int:customer_id>', methods=['POST'])
def unblock_customer1(customer_id):
    customer = User.query.get(customer_id)  
    if customer:
        customer.blocked = 0 
        db.session.commit()  

        log_entry = Log(
            timestamp=datetime.now(),  
            action=f"Customer '{customer.username}' unblocked",  
            username='admin'  
        )
        db.session.add(log_entry) 
        db.session.commit()  
    return redirect(url_for('admin_dashboard'))  

@app.route('/admin/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer = User.query.get(customer_id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/accept_professional/<int:professional_id>', methods=['POST'])
def accept_professional(professional_id):
    professional = User.query.get(professional_id)  
    if professional:
        professional.approval = True  
        professional.blocked = False
        db.session.commit()  

        log_entry = Log(
            timestamp=datetime.now(), 
            action=f"Professional '{professional.username}' approved",  
            username='admin'  
        )
        db.session.add(log_entry)  
        db.session.commit() 
    return redirect(url_for('admin_search'))  

@app.route('/admin/block_professional/<int:professional_id>', methods=['POST'])
def block_professional(professional_id):
    professional = User.query.get(professional_id)  
    if professional:
        professional.blocked = True  
        professional.approval = False
        db.session.commit() 

        log_entry = Log(
            timestamp=datetime.now(), 
            action=f"Professional '{professional.username}' rejected",  
            username='admin' 
        )
        db.session.add(log_entry)  
        db.session.commit()  
    return redirect(url_for('admin_search')) 

@app.route('/edit_service_request/<int:request_id>', methods=['POST'])
def edit_service_request(request_id):
    request_to_edit = ServiceRequest.query.get(request_id)  
    if request_to_edit:
        date_of_request_str = request.form['requested_date']
        request_to_edit.date_of_request = datetime.strptime(date_of_request_str, '%Y-%m-%d').date() 
        request_to_edit.remarks = request.form['remarks']
        db.session.commit()  
    return redirect(url_for('customer_dashboard'))  

@app.route('/service_professional_dashboard')
def service_professional_dashboard():
    today = datetime.today().date()
    current_professional_id = session.get('user_id')

    professional = User.query.filter_by(id=current_professional_id, role='service_professional').first()
    if not current_professional_id:
        return redirect(url_for('any_page_noaccess'))
    #add this once done:  and professional.approval == 1 and professional.blocked == 0
    if professional and professional.approval == 1 and professional.blocked == 0:
        today_services = ServiceRequest.query.join(Service).filter(
            Service.is_active == True,
            ServiceRequest.service_status != 'Closed',
            Service.name == professional.service_name 
        ).all()

        closed_services = ServiceRequest.query.join(Service).filter(
            ServiceRequest.service_status == 'Closed',
            Service.name == professional.service_name  
        ).all()

        return render_template('service_professional_dashboard.html', today_services=today_services, closed_services=closed_services, professional=professional)
    else:
        return redirect(url_for('service_professional_blocked'))  

@app.route('/update_profile', methods=['POST'])
def update_profile():
    current_professional_id = session.get('user_id')

    professional = User.query.get(current_professional_id)

    professional.name = request.form['name']
    professional.email = request.form['email']
    professional.phone_number = request.form['phone_number']
    professional.address = request.form['address']
    professional.pincode = request.form['pincode']
    professional.experience = request.form['experience']
    professional.service_name = request.form['service_name']

    db.session.commit()

    log_entry = Log(
            timestamp=datetime.now(),  
            action=f"Professional '{professional.username}' updated their profile",  
            username=professional.username  
        )
    db.session.add(log_entry)  
    db.session.commit()  

    return redirect(url_for('service_professional_dashboard'))

@app.route('/update_profile_customer', methods=['POST'])
def update_profile_customer():
    current_customer_id = session.get('user_id')

    customer = User.query.get(current_customer_id)

    customer.name = request.form['name']
    customer.email = request.form['email']
    customer.phone_number = request.form['phone_number']
    customer.address = request.form['address']
    customer.pincode = request.form['pincode']

    db.session.commit()

    return redirect(url_for('customer_dashboard'))

@app.route('/accept_service/<int:service_id>', methods=['POST'])
def accept_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if service_request:
        service_request.professional_id = session.get('user_id')
        service_request.service_status = 'Assigned' 
        db.session.commit()
    return redirect(url_for('service_professional_dashboard'))

@app.route('/reject_service/<int:service_id>', methods=['POST'])
def reject_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if service_request:
        db.session.delete(service_request) 
        db.session.commit()
    return redirect(url_for('service_professional_dashboard'))

@app.route('/customer_dashboard')
def customer_dashboard():
    user_id = session.get('user_id')
    user = User.query.get(user_id)  
    if not user_id:
        return redirect(url_for('any_page_noaccess'))
    if user and user.blocked == 1:
        return redirect(url_for('customer_blocked'))  

    customer = User.query.filter_by(id=user_id, role='customer').first()
    
    services = Service.query.filter_by(is_active=True).all()  

    service_history = ServiceRequest.query \
        .join(Service, ServiceRequest.service_id == Service.id) \
        .join(User, ServiceRequest.customer_id == User.id) \
        .filter(ServiceRequest.customer_id == user_id) \
        .all()
    
    top_rated_professionals = User.query \
        .filter_by(role='service_professional') \
        .filter(User.rating != 0) \
        .order_by(User.rating.desc()) \
        .limit(10) \
        .all()  

    return render_template('customer_dashboard.html', customer=customer, services=services, service_history=service_history, user=user, top_rated_professionals=top_rated_professionals)

@app.route('/book_service', methods=['POST'])
def book_service():
    service_id = request.form['service_id']
    date_of_request_str = request.form['date_of_request']
    remarks = request.form['remarks']
    
    date_of_request = datetime.strptime(date_of_request_str, '%Y-%m-%d').date()  

    customer_id = session.get('user_id')
    customer = User.query.get(customer_id)
    service = Service.query.filter_by(id=service_id).first()
    service_price = service.price

    new_request = ServiceRequest(
        service_id=service_id,
        customer_id=customer_id,
        professional_id=None,  
        service_status='Requested',
        date_of_request=date_of_request,
        remarks=remarks,
        cost=service_price
    )

    db.session.add(new_request)
    db.session.commit()
    log_entry = Log(
        timestamp=datetime.now(),  
        action=f"Service '{service.name}' booked by customer '{customer.username}' successfully",
        username=customer.username  
    )
    db.session.add(log_entry)  
    db.session.commit()  
    return redirect(url_for('customer_dashboard'))

@app.route('/book_service1', methods=['POST'])
def book_service1():
    service_id = request.form['service_id']
    service = Service.query.get(service_id)
    date_of_request_str = request.form['date_of_request']
    remarks = request.form['remarks']
    cost = request.form['payment_amount']
    
    date_of_request = datetime.strptime(date_of_request_str, '%Y-%m-%d').date() 

    customer_id = session.get('user_id')
    customer = User.query.get(customer_id)

    new_request = ServiceRequest(
        service_id=service_id,
        customer_id=customer_id,
        professional_id=None,  
        service_status='Requested',
        date_of_request=date_of_request,
        remarks=remarks,
        cost=cost
    )

    db.session.add(new_request)
    db.session.commit()
    log_entry = Log(
        timestamp=datetime.now(),  
        action=f"Service '{service.name}' booked by customer '{customer.username}' successfully",
        username=customer.username 
    )
    db.session.add(log_entry)  
    db.session.commit()  
    return redirect(url_for('customer_dashboard'))

@app.route('/customer_search', methods=['GET', 'POST'])
def customer_search():
    user_id = session.get('user_id')

    unique_services = Service.query.distinct(Service.name).all()

    service_history = ServiceRequest.query \
        .join(Service, ServiceRequest.service_id == Service.id) \
        .join(User, ServiceRequest.customer_id == User.id) \
        .filter(ServiceRequest.customer_id == user_id) \
        .all()

    return render_template('customer_search.html', services=unique_services, service_history=service_history)

@app.route('/close_service_request/<int:request_id>', methods=['POST'])
def close_service_request(request_id):
    request_to_close = ServiceRequest.query.get(request_id)
    
    if request_to_close:
        request_to_close.service_status = 'Closed'  
        request_to_close.remarks = request.form.get('remarks', '')  
        request_to_close.date_of_completion = datetime.now()
        
        rating = request.form.get('rating')  
        
        if rating:
            rating_value = int(rating)  
            professional_id = request_to_close.professional_id
            if professional_id:  
                professional = User.query.get(professional_id)  
            
                if professional: 
                    if professional.rating and professional.rating != 0:
                        new_rating = round((professional.rating + rating_value) / 2)
                    else:
                        new_rating = rating_value
                
                    professional.rating = new_rating 
                
                    db.session.commit()  
        
        db.session.commit()  
    
    return redirect(url_for('customer_dashboard')) 


@app.route('/close_service1/<int:service_id>', methods=['POST'])
def close_service1(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if service_request and service_request.service_status == 'Assigned':
        service_request.service_status = 'Closed' 
        service_request.date_of_completion = datetime.now()  
        db.session.commit() 

    return redirect(url_for('service_professional_dashboard'))  

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
        
        new_user = User(
        name=name,
        username=username,
        email=email,
        phone_number=phone_number,
        address=address,
        pincode=pincode,
        role='admin',  
        blocked=False, 
        approval=None,  
        profile_photo=None  
        )
    
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('home'))  
    
    return render_template('admin_login.html')

@app.route('/admin/new_service', methods=['POST'])
def new_service():
    name = request.form['name']
    description = request.form['description']
    base_price = request.form['base_price']
    time_required = request.form['time_required']
    is_active = request.form['is_active'] == 'true'  
    category = request.form['category']  

    new_service = Service(
        name=name,
        description=description,
        price=base_price,
        time_required=time_required,
        is_active=is_active,
        category=category
    )

    db.session.add(new_service)
    db.session.commit()  

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_service/<int:service_id>', methods=['POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if service:
        service.name = request.form['name']
        service.description = request.form['description']
        service.price = request.form['base_price']
        service.time_required = request.form['time_required']
        service.is_active = request.form['is_active'] == 'true' 
        service.category = request.form['category']  

        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Service.query.get(service_id)
    
    if service:
        service_name_to_delete = service.name
        
        related_requests = ServiceRequest.query.filter_by(service_id=service_id).all()
        for request in related_requests:
            db.session.delete(request)
        
        db.session.commit() 

        db.session.delete(service)
        db.session.commit()  

        users_to_delete = User.query.filter_by(service_name=service_name_to_delete).all()
        
        for user in users_to_delete:
            db.session.delete(user)
        
        db.session.commit()  
        log_entry = Log(
                timestamp=datetime.now(),  
                action=f"Service '{service_name_to_delete}' deleted along with {len(related_requests)} requests and {len(users_to_delete)} professional",  
                username='admin'  
        )
        db.session.add(log_entry) 
        db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_professional/<int:professional_id>', methods=['POST'])
def approve_professional(professional_id):
    professional = User.query.get(professional_id)
    if professional:
        professional.approval = True 
        professional.blocked = False 
        db.session.commit()
        log_entry = Log(
            timestamp=datetime.now(),  
            action=f"Professional '{professional.username}' approved",  
            username='admin' 
        )
        db.session.add(log_entry) 
        db.session.commit()  
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_professional/<int:professional_id>', methods=['POST'])
def reject_professional(professional_id):
    professional = User.query.get(professional_id)
    if professional:
        professional.blocked = True    
        professional.approval = False   
        db.session.commit()
        log_entry = Log(
            timestamp=datetime.now(),
            action=f"Professional '{professional.username}' rejected", 
            username='admin'  
        )
        db.session.add(log_entry)  
        db.session.commit() 
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_professional/<int:professional_id>', methods=['POST'])
def delete_professional(professional_id):
    professional = User.query.get(professional_id)
    if professional:
        db.session.delete(professional)  
        db.session.commit()
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
                results = Service.query.filter(Service.is_active == True).all()  
            elif search_text.lower() == 'inactive':
                results = Service.query.filter(Service.is_active == False).all()  
            else:
                results = Service.query.filter(Service.name.contains(search_text)).all()  

        elif search_type == 'customer':
            results = User.query.filter(User.name.contains(search_text), User.role == 'customer').all()

        elif search_type == 'professional':
            results = User.query.filter(User.name.contains(search_text), User.role == 'service_professional').all()

        elif search_type == 'service_request':
            if search_text.lower() == 'assigned':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Assigned').all()  
            elif search_text.lower() == 'closed':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Closed').all()  
            elif search_text.lower() == 'requested':
                results = ServiceRequest.query.filter(ServiceRequest.service_status == 'Requested').all() 
            else:
                results = ServiceRequest.query.filter(ServiceRequest.remarks.contains(search_text)).all() 

    return render_template('admin_search.html', results=results, search_type=search_type, search_text=search_text)

@app.route('/service_professional_search', methods=['GET', 'POST'])
def service_professional_search():
    results = []
    if request.method == 'POST':
        search_by = request.form['search_by']
        search_text = request.form['search_text']

        if search_by == 'date':
            results = ServiceRequest.query.join(User, ServiceRequest.customer_id == User.id).filter(
                func.date(ServiceRequest.date_of_request) == search_text  
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
    service_requests = ServiceRequest.query.all()

    service_counts = {}
    completion_counts = {'Requested': 0, 'Assigned': 0, 'Closed': 0}
    revenue_data = {}

    for request in service_requests:
        if request.service_status in completion_counts:
            completion_counts[request.service_status] += 1

        service_name = request.service.name
        if request.cost is not None:  
            revenue_data[service_name] = revenue_data.get(service_name, 0) + request.cost

    services = Service.query.all()
    for service in services:
        service_name = service.name
        service_counts[service_name] = service_counts.get(service_name, 0) + 1

    return render_template('admin_summary.html', 
                           service_counts=service_counts, 
                           completion_counts=completion_counts, 
                           revenue_data=revenue_data)  

@app.route('/service_professional_summary')
def service_professional_summary():
    professional_id = session.get('user_id')

    service_requests = ServiceRequest.query.filter_by(professional_id=professional_id).all()

    completion_counts = {'Requested': 0, 'Assigned': 0, 'Closed': 0}
    customer_request_counts = {}

    for request in service_requests:
        if request.service_status in completion_counts:
            completion_counts[request.service_status] += 1

        customer = User.query.filter_by(id=request.customer_id).first()
        customer_name = customer.name if customer else 'Unknown'

        if customer_name not in customer_request_counts:
            customer_request_counts[customer_name] = 0
        customer_request_counts[customer_name] += 1

    service_name = service_requests[0].service.name if service_requests else 'No service assigned'

    return render_template('service_professional_summary.html', 
                           service_name=service_name,
                           customer_request_counts=customer_request_counts, 
                           completion_counts=completion_counts)

@app.route('/customer_summary')
def customer_summary():
    customer_id = session.get('user_id')
    
    if not customer_id:
        return redirect(url_for('login'))

    service_requests = ServiceRequest.query.filter_by(customer_id=customer_id).all()

    service_counts = {}
    completion_counts = {'Requested': 0, 'Assigned': 0, 'Closed': 0}
    revenue_data = {} 

    for request in service_requests:
        if request.service_status in completion_counts:
            completion_counts[request.service_status] += 1

        service_name = request.service.name  

        service_counts[service_name] = service_counts.get(service_name, 0) + 1

        if request.cost is not None:
            revenue_data[service_name] = revenue_data.get(service_name, 0) + request.cost

    return render_template('customer_summary.html', 
                           service_counts=service_counts, 
                           completion_counts=completion_counts,
                           revenue_data=revenue_data)

@app.route('/search_services', methods=['POST'])
def search_services():
    service_name = request.form.get('service_name')
    search_text = request.form.get('search_text')
    
    # Initialize the query
    user_id = session.get('user_id')  # Replace with actual user ID from session or context
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