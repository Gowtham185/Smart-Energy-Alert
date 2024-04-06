from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['STATIC_FOLDER'] = STATIC_FOLDER

# Function to send email notification
def send_email_notification(username, house_email, usage_type, usage, house_number):
    # Email configuration
    sender_email = 'gowthambaskar185@gmail.com'  # Replace with your email
    password = 'pmmd xegr jlfg qczt'  # Replace with your email password

    # Create message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = ', '.join([username, house_email])
    message['Subject'] = f"Electricity Usage Alert - House {house_number} - {usage_type.capitalize()}"

    # Email body
    body = f"Hello Tenant!\n\nHouse {house_number} {usage_type} electricity usage has exceeded the threshold. Usage: {usage} kWh.\n\nRegards,\nWinnovate systems"
    message.attach(MIMEText(body, 'plain'))

    # Send email with timeout
    timeout = 20  # Set timeout value (in seconds)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=timeout) as server:
            server.starttls()
            server.login(sender_email, password)
            text = message.as_string()
            server.sendmail(sender_email, [username, house_email], text)
        print(f"Email sent successfully for House {house_number}")
    except (socket.timeout, smtplib.SMTPConnectError) as e:
        print(f"Error: {e}")

# Function to generate random electricity reading and check if it exceeds threshold
def generate_electricity_reading():
    return random.randint(50, 100)  # Current usage between 50 to 100

# Function to update current usage every 30 seconds for all houses
def update_current_usage():
    while True:
        for house_number in range(1, 6):
            current_reading = generate_electricity_reading()
            usage_data[house_number]['daily'] += current_reading  # Update daily usage
            usage_data[house_number]['monthly'] += current_reading  # Update monthly usage
            
            # Check if daily threshold exceeded
            #if usage_data[house_number]['daily'] >= 250:
                # Notify manager and tenant
                #send_email_notification('baskarg@uwindsor.ca', usage_data[house_number]['email'], 'daily', usage_data[house_number]['daily'], house_number)
                # Reset daily usage
                #usage_data[house_number]['daily'] = random.randint(200, 300)
            
            # Check if monthly threshold exceeded
            if usage_data[house_number]['monthly'] >= 6000:
                # Notify manager and tenant
                send_email_notification('baskarg@uwindsor.ca', usage_data[house_number]['email'], 'monthly', usage_data[house_number]['monthly'], house_number)
                # Reset monthly usage
                usage_data[house_number]['monthly'] = random.randint(5900, 6200)
        time.sleep(30)

# Start thread to update current usage
usage_data = {
    1: {'daily': random.randint(230, 270), 'monthly': random.randint(5800, 6200), 'email': 'saisrin@uwindsor.ca'},
    2: {'daily': random.randint(230, 270), 'monthly': random.randint(5800, 6200), 'email': 'amjikar@uwindsor.ca'},
    3: {'daily': random.randint(230, 270), 'monthly': random.randint(5800, 6200), 'email': 'justin4@uwindsor.ca'},
    4: {'daily': random.randint(230, 270), 'monthly': random.randint(5800, 6200), 'email': 'venkat44@uwindsor.ca'},
    5: {'daily': random.randint(230, 270), 'monthly': random.randint(5800, 6200), 'email': 'jayapra6@uwindsor.ca'}
}  # Initial usage data for all houses

# SQLite database connection
conn = sqlite3.connect('user_credentials.db')
cursor = conn.cursor()

# Create users table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
conn.commit()

# Ensure existing usernames and passwords are inserted into the database
users = {'baskarg@uwindsor.ca': 'test2024'}
for username, password in users.items():
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))
conn.commit()

# Create house table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS house
                (house_number INTEGER PRIMARY KEY, house_email TEXT UNIQUE)''')
conn.commit()

# Insert data into the house table
houses = [
    (1, 'saisrin@uwindsor.ca'),
    (2, 'amjikar@uwindsor.ca'),
    (3, 'justin4@uwindsor.ca'),
    (4, 'venkat44@uwindsor.ca'),
    (5, 'jayapra6@uwindsor.ca')
]
cursor.executemany("INSERT OR IGNORE INTO house (house_number, house_email) VALUES (?, ?)", houses)
conn.commit()

# Close the database connection
conn.close()

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('user_credentials.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = username
            current_usage_thread = threading.Thread(target=update_current_usage)
            current_usage_thread.daemon = True
            current_usage_thread.start()
            return redirect('/dashboard')
        else:
            return render_template('login.html', message='Invalid username or password')
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        # Check daily and monthly usage for all houses
        # daily_usages = {house_number: usage_data[house_number]['daily'] for house_number in range(1, 6)}
        monthly_usages = {house_number: usage_data[house_number]['monthly'] for house_number in range(1, 6)}
        #daily_exceeded = {house_number: daily_usage >= 250 for house_number, daily_usage in daily_usages.items()}
        monthly_exceeded = {house_number: monthly_usage >= 6000 for house_number, monthly_usage in monthly_usages.items()}
        return render_template('dashboard.html', username=session['username'], monthly_usages=monthly_usages, monthly_exceeded=monthly_exceeded)
    return redirect('/')

@app.route('/api/monthly-usage')
def get_monthly_usage():
    monthly_usages = {house_number: usage_data[house_number]['monthly'] for house_number in range(1, 6)}
    return jsonify(monthly_usages)

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
