from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
import joblib
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__, static_folder='static')
app.secret_key = 'forestguard_secret_key'  # Required for session and flash

# Paths for models and data
USERS_FILE = 'users.json'
CLASSIFICATION_MODEL_PATH = 'fire_classification.pkl'
SEVERITY_MODEL_PATH = 'fire_severity.pkl'
SCALER_PATH = 'scaler.pkl'
NEWS_API_KEY ='YOUR_OWN_API_KEY_GOES_HERE'

# Load models and scaler
classification_model = joblib.load(CLASSIFICATION_MODEL_PATH)
severity_model = joblib.load(SEVERITY_MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# Initialize user file
def initialize_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)

# Load users from JSON file
def load_users():
    with open(USERS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# Save users to JSON file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/news')
def news():
    url = (
        'https://newsapi.org/v2/everything?'
        'q="forest fire" OR wildfire OR bushfire&'
        'sortBy=publishedAt&'
        'language=en&'
        'pageSize=30&'  # fetch more to allow filtering
        'excludeDomains=imdb.com,hollywoodreporter.com,screenrant.com,deadline.com,healthline.com'
        f'&apiKey={NEWS_API_KEY}'
    )

    response = requests.get(url)
    data = response.json()

    allowed_keywords = ['forest fire', 'wildfire', 'bushfire']
    banned_keywords = ['diet', 'fitness', 'movie', 'celebrity', 'fashion', 'weight', 'entertainment']

    unique_titles = set()
    filtered_articles = []

    if data.get('status') == 'ok':
        for article in data.get('articles', []):
            title = article.get('title', '').strip().lower()
            description = article.get('description', '').strip().lower()

            if title in unique_titles:
                continue  # Skip duplicates

            if any(kw in title or kw in description for kw in allowed_keywords):
                if not any(bad_kw in title or bad_kw in description for bad_kw in banned_keywords):
                    unique_titles.add(title)
                    filtered_articles.append(article)

    return render_template('news.html', articles=filtered_articles[:6])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        user = next((user for user in users if user['username'] == username), None)
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('d1'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        users = load_users()
        
        if any(user['username'] == username for user in users):
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        hashed_password = generate_password_hash(password)
        new_user = {'username': username, 'email': email, 'password': hashed_password}
        users.append(new_user)
        save_users(users)
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/d1')
def d1():
    if 'username' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    return render_template('d1.html', username=session['username'])

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    try:
        temperature = float(request.form['temperature'])
        rain = float(request.form['rain'])
        ffmc = float(request.form['ffmc'])
        dmc = float(request.form['dmc'])
        isi = float(request.form['isi'])
        
        input_data = np.array([[temperature, rain, ffmc, dmc, isi]])
        input_data_scaled = scaler.transform(input_data)
        
        fire_prediction = classification_model.predict(input_data_scaled)[0]
        
        if fire_prediction == 1:
            severity = severity_model.predict(input_data_scaled)[0]
            
            if severity < 10:
                severity_label = "🔥 Fire Risk! Severity: Low"
            elif  10<= severity < 20:
                severity_label = "🔥 Fire Risk! Severity: Moderate"
            elif 20<= severity < 40:
                severity_label = "🔥 Fire Risk! Severity: High"
            else:
                severity_label = "🔥 Fire Risk! Severity: Extreme"
            
            severity_output = f"{severity_label} (Severity Score: {severity:.2f})"
        else:
            severity_output = " No Fire (Severity Score: 0.00)"
        
        return render_template('d1.html', 
                               username=session['username'], 
                               prediction=severity_output)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('d1'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ == '__main__':
    initialize_users_file()
    app.run(debug=True)
