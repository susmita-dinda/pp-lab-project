import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import uuid
from extensions import db, login_manager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///donations.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models and forms
from models import User, Donation
from forms import LoginForm, RegistrationForm, DonationForm, ProfileForm
from utils import allowed_file, save_image

# Define user_loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Serve uploaded files from the UPLOAD_FOLDER if it's not in the static directory
if not app.config['UPLOAD_FOLDER'].startswith('static/'):
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')

    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard based on role"""
    if current_user.role == 'donor':
        return redirect(url_for('donor_dashboard'))
    else:
        return redirect(url_for('receiver_dashboard'))

@app.route('/donor/dashboard')
@login_required
def donor_dashboard():
    """Donor dashboard route"""
    if current_user.role != 'donor':
        flash('Access denied. You are not registered as a donor.', 'danger')
        return redirect(url_for('dashboard'))

    # Get all donations made by this donor
    donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()

    # Get a list of all receivers for the donation form
    receivers = User.query.filter_by(role='receiver').all()

    return render_template('donor_dashboard.html', donations=donations, receivers=receivers)

@app.route('/receiver/dashboard')
@login_required
def receiver_dashboard():
    """Receiver dashboard route"""
    if current_user.role != 'receiver':
        flash('Access denied. You are not registered as a receiver.', 'danger')
        return redirect(url_for('dashboard'))

    # Get all donations made to this receiver
    donations = Donation.query.filter_by(receiver_id=current_user.id).order_by(Donation.created_at.desc()).all()

    return render_template('receiver_dashboard.html', donations=donations)

@app.route('/create-donation', methods=['GET', 'POST'])
@login_required
def create_donation():
    """Create a new donation"""
    if current_user.role != 'donor':
        flash('Only donors can create donations.', 'danger')
        return redirect(url_for('dashboard'))

    form = DonationForm()
    # Populate receiver choices
    form.receiver.choices = [(str(r.id), r.username) for r in User.query.filter_by(role='receiver').all()]

    if form.validate_on_submit():
        try:
            # Handle image upload
            image_filename = None
            if form.image.data:
                image_filename = save_image(form.image.data)

            # Create new donation
            donation = Donation(
                title=form.title.data,
                description=form.description.data,
                image=image_filename,
                donor_id=current_user.id,
                receiver_id=int(form.receiver.data),
                status='pending'
            )

            db.session.add(donation)
            db.session.commit()
            flash('Donation created successfully!', 'success')
            return redirect(url_for('donor_dashboard'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating donation: {str(e)}")
            flash('An error occurred while creating your donation.', 'danger')

    return render_template('create_donation.html', form=form)

@app.route('/donation/<int:donation_id>')
@login_required
def donation_detail(donation_id):
    """View details of a specific donation"""
    donation = Donation.query.get_or_404(donation_id)

    # Check if the user has access to this donation
    if current_user.id != donation.donor_id and current_user.id != donation.receiver_id:
        flash('You do not have permission to view this donation.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('donation_detail.html', donation=donation)

@app.route('/donation/<int:donation_id>/update-status', methods=['POST'])
@login_required
def update_donation_status(donation_id):
    """Update the status of a donation"""
    donation = Donation.query.get_or_404(donation_id)

    # Only the receiver can mark donations as received
    if current_user.id != donation.receiver_id:
        flash('You do not have permission to update this donation status.', 'danger')
        return redirect(url_for('dashboard'))

    new_status = request.form.get('status')
    if new_status in ['pending', 'received']:
        donation.status = new_status
        donation.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Donation status updated successfully.', 'success')
    else:
        flash('Invalid status.', 'danger')

    return redirect(url_for('donation_detail', donation_id=donation_id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', form=form)

@app.route('/donations-history')
@login_required
def donations_history():
    """View history of donations"""
    if current_user.role == 'donor':
        donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    else:
        donations = Donation.query.filter_by(receiver_id=current_user.id).order_by(Donation.created_at.desc()).all()

    return render_template('donations_history.html', donations=donations)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('error.html', error="Server error"), 500

@app.context_processor
def inject_current_year():
    """Add current_year to all template contexts"""
    return {'current_year': datetime.now().year}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
