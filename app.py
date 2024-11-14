import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd

app = Flask(__name__)

# Load the secret key from environment variable
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key')  # Change this to a random secret key in production
login_manager = LoginManager()
login_manager.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load user data from CSV
def load_users():
    return pd.read_csv('users.csv')

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    user_data = users[users['username'] == user_id]
    if not user_data.empty:
        return User(user_data['username'].values[0], user_data['role'].values[0])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        user = users[(users['username'] == username) & (users['password'] == password)]
        if not user.empty:
            user_obj = User(username, user['role'].values[0])
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    # Ensure the file exists before trying to send it
    upload_folder = 'uploads'
    if os.path.exists(os.path.join(upload_folder, filename)):
        return send_from_directory(upload_folder, filename, as_attachment=True)
    else:
        flash('File not found', 'danger')
        return redirect(url_for('files'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/files', methods=['GET', 'POST'])
@login_required
def files():
    if request.method == 'POST':
        # Allow only admin to upload files
        if current_user.role != 'admin':
            flash('You do not have permission to upload files.', 'danger')
            return redirect(url_for('files'))
        
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Save the file
        upload_folder = 'uploads'  # Specify your upload folder
        os.makedirs(upload_folder, exist_ok=True)  # Create the folder if it doesn't exist
        file_path = os.path.join(upload_folder, file.filename)
        
        # Check for file overwriting
        if os.path.exists(file_path):
            flash('File already exists. Please rename the file and try again.', 'danger')
            return redirect(request.url)
        
        file.save(file_path)
        flash('File successfully uploaded', 'success')
        return redirect(url_for('files'))
    
    # Display files uploaded by admin
    uploaded_files = os.listdir('uploads')
    return render_template('files.html', files=uploaded_files)

if __name__ == '__main__':
    # Run the app with Gunicorn in production
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',  5000)), debug=False)  # Set debug to False in production