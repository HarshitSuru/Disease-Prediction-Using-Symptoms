from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file

from flask import Flask, request, render_template, redirect, url_for, session, flash
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import openpyxl
import nltk
from nltk.corpus import wordnet
from collections import Counter
import operator
import wikipedia
import random
import string
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User # Import db and User from models.py

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')


# Initialize extensions
db.init_app(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if user is not authenticated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Function to generate a random 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Function to send OTP email
def send_verification_email(email, otp):
    msg = Message("MediCURE - Email Verification Code", recipients=[email])
    msg.body = f"Your verification code is: {otp}\n\nThis code will expire in 10 minutes."
    mail.send(msg)

# Load datasets and model
df_comb = pd.read_csv('Dataset/dis_sym_dataset_comb.csv')
df_norm = pd.read_csv('Dataset/dis_sym_dataset_norm.csv')
model = pickle.load(open('model_saved', 'rb'))

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if username or email already exists
        user_by_username = User.query.filter_by(username=username).first()
        if user_by_username:
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))

        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            flash('Email address already registered', 'danger')
            return redirect(url_for('signup'))

        # Basic email validation
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            flash('Invalid email address', 'danger')
            return redirect(url_for('signup'))

        # Generate OTP and store user details in session
        otp = generate_otp()
        session['registration_data'] = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password, method='pbkdf2:sha256'),
            'otp': otp,
            'created_at': pd.Timestamp.now().timestamp()  # Store timestamp for expiry check
        }

        try:
            # Send verification email
            send_verification_email(email, otp)
            flash('Verification code has been sent to your email.', 'success')
            return redirect(url_for('verify_otp'))
        except Exception as e:
            app.logger.error(f"Failed to send email: {str(e)}")
            flash('Failed to send verification email. Please try again.', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    # Check if there's registration data in session
    if 'registration_data' not in session:
        flash('Registration session expired. Please register again.', 'danger')
        return redirect(url_for('signup'))
    
    reg_data = session['registration_data']
    
    # Check if OTP has expired (10 minutes)
    if pd.Timestamp.now().timestamp() - reg_data['created_at'] > 600:  # 600 seconds = 10 minutes
        session.pop('registration_data', None)
        flash('Verification code expired. Please register again.', 'danger')
        return redirect(url_for('signup'))
    
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if user_otp == reg_data['otp']:
            # Create new user
            new_user = User(
                username=reg_data['username'],
                email=reg_data['email'],
                password=reg_data['password']
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Remove registration data from session
            session.pop('registration_data', None)
            
            # Log user in
            login_user(new_user)
            flash('Your account has been created successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')
    
    # For GET request or invalid OTP
    return render_template('verify_otp.html', email=reg_data['email'])

@app.route('/resend-otp', methods=['GET'])
def resend_otp():
    if 'registration_data' not in session:
        flash('Registration session expired. Please register again.', 'danger')
        return redirect(url_for('signup'))
    
    reg_data = session['registration_data']
    
    # Generate new OTP
    new_otp = generate_otp()
    session['registration_data']['otp'] = new_otp
    session['registration_data']['created_at'] = pd.Timestamp.now().timestamp()
    
    try:
        # Send verification email
        send_verification_email(reg_data['email'], new_otp)
        flash('New verification code has been sent to your email.', 'success')
    except Exception as e:
        app.logger.error(f"Failed to send email: {str(e)}")
        flash('Failed to send verification email. Please try again.', 'danger')
    
    return redirect(url_for('verify_otp'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_identifier = request.form.get('login_identifier')
        password = request.form.get('password')
        
        # Try to find user by username or email
        user = User.query.filter((User.username == login_identifier) | (User.email == login_identifier)).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username/email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/predict')
@login_required
def predict():
    return render_template('symptoms_input.html')

@app.route('/process-symptoms', methods=['POST'])
@login_required
def process_symptoms():
    user_symptoms = request.form.get('symptoms', '').lower().split(',')
    user_symptoms = [s.strip() for s in user_symptoms if s.strip()]
    
    dataset_symptoms = list(df_comb.columns[1:])
    found_symptoms = []

    for user_sym in user_symptoms:
        for data_sym in dataset_symptoms:
            if user_sym in data_sym.lower():
                found_symptoms.append(data_sym)

    if not found_symptoms:
        flash('No matching symptoms found. Please try again with different symptoms.', 'warning')
        return redirect(url_for('predict'))

    # Create sample vector for prediction based on found symptoms
    sample_x = [1 if sym in found_symptoms else 0 for sym in dataset_symptoms]
    
    # Get disease probabilities based on current symptoms
    output = model.predict_proba([sample_x])
    diseases = sorted(set(df_comb['label_dis']))
    
    # Get top diseases based on probability
    topk_diseases = output[0].argsort()[-10:][::-1]  # Get top 10 diseases
    
    # Calculate weighted symptoms based on disease probabilities
    symptom_weights = {}
    for idx in topk_diseases:
        disease = diseases[idx]
        probability = output[0][idx]  # Disease probability
        
        # Get symptoms associated with this disease
        disease_row = df_norm[df_norm['label_dis'] == disease].iloc[0]
        
        # Weight each symptom by the disease probability
        for i, symptom in enumerate(dataset_symptoms):
            if disease_row[symptom] == 1 and symptom not in found_symptoms:
                if symptom in symptom_weights:
                    symptom_weights[symptom] += probability
                else:
                    symptom_weights[symptom] = probability
    
    # Sort symptoms by weight and get top 15
    additional_symptoms = [sym for sym, weight in 
                          sorted(symptom_weights.items(), 
                                key=operator.itemgetter(1), reverse=True)[:15]]
    
    session['found_symptoms'] = found_symptoms
    session['additional_symptoms'] = additional_symptoms

    return redirect(url_for('additional_symptoms'))

@app.route('/additional-symptoms')
@login_required
def additional_symptoms():
    return render_template('additional_symptoms.html', 
                           original_symptoms=session.get('found_symptoms', []),
                           additional_symptoms=enumerate(session.get('additional_symptoms', [])))

@app.route('/process-additional', methods=['POST'])
@login_required
def process_additional():
    selected_symptoms = request.form.getlist('symptoms')
    all_symptoms = session.get('found_symptoms', []) + selected_symptoms

    dataset_symptoms = list(df_comb.columns[1:])
    sample_x = [1 if sym in all_symptoms else 0 for sym in dataset_symptoms]

    output = model.predict_proba([sample_x])
    diseases = sorted(set(df_comb['label_dis']))
    topk = output[0].argsort()[-5:][::-1]

    conditions = []
    for idx in topk:
        disease = diseases[idx]
        probability = round(output[0][idx] * 100, 1)

        matching_symptoms = []
        disease_row = df_norm[df_norm['label_dis'] == disease].iloc[0]
        for sym in all_symptoms:
            if sym in dataset_symptoms and disease_row[sym] == 1:
                matching_symptoms.append(sym)

        desc = get_wikipedia_description(disease)

        conditions.append({
            'name': disease,
            'desc': desc or f"Based on your symptoms, you may be experiencing {disease}.",
            'probability': probability,
            'matching_symptoms': matching_symptoms[:10]
        })

    session['conditions'] = conditions
    return redirect(url_for('results'))

@app.route('/results')
@login_required
def results():
    return render_template('results.html', conditions=session.get('conditions', []))

@app.route('/treatment', methods=['POST'])
@login_required
def treatment():
    condition = request.form.get('dis')
    workbook = openpyxl.load_workbook('cure_minor.xlsx')
    worksheet = workbook['Sheet1']

    remedies = []
    for row in worksheet.iter_rows(values_only=True):
        if condition in row:
            remedies = [r.strip() for r in str(row[1]).split(',') if r.strip()]
            break
    return render_template('treatment.html', condition=condition, remedies=remedies)

def get_wikipedia_description(disease):
    try:
        if not hasattr(get_wikipedia_description, 'cache'):
            get_wikipedia_description.cache = {}
        
        if disease in get_wikipedia_description.cache:
            return get_wikipedia_description.cache[disease]

        result = wikipedia.summary(disease, sentences=2)
        get_wikipedia_description.cache[disease] = result
        return result
    except:
        return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables if they don't exist
    app.run(debug=True)
