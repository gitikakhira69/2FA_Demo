from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyotp
import bcrypt
import time
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'a_very_random_secret_key_12345'

# --- User Data (Demo purposes) ---
# username -> {'password': hashed, 'email': email}
USERS = {}

# --- OTP Setup ---
MAX_ATTEMPTS = 3
OTP_EXPIRY = 120  # seconds
OTP_TIMESTAMP = {}
CURRENT_OTP = {}

# --- Email Configuration ---
SENDER_EMAIL = 'gitikagithub@gmail.com'
SENDER_PASSWORD = 'rnhy xjdd rknx zfpd'  # Gmail App Password

def send_otp_email(recipient_email, otp):
    subject = 'Your 2FA OTP Code'
    body = f'Your OTP is: {otp}\nIt is valid for 2 minutes.'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"OTP sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# --- Routes ---
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if username in USERS:
            flash("Username already exists!")
            return redirect(url_for('register'))

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        USERS[username] = {'password': hashed_pw, 'email': email}

        flash("Registration successful! Please login.")
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in USERS and bcrypt.checkpw(password.encode(), USERS[username]['password']):
        session['username'] = username

        # Generate OTP
        totp = pyotp.TOTP(pyotp.random_base32())
        otp = totp.now()
        CURRENT_OTP[username] = otp
        OTP_TIMESTAMP[username] = time.time()

        # Send OTP via email
        send_otp_email(USERS[username]['email'], otp)

        flash("OTP sent to your email!")
        return redirect(url_for('two_factor'))
    else:
        flash("Invalid username or password!")
        return redirect(url_for('home'))

@app.route('/two_factor', methods=['GET', 'POST'])
def two_factor():
    if 'username' not in session:
        flash("Please login first.")
        return redirect(url_for('home'))

    username = session['username']
    attempts = session.get('otp_attempts', 0)

    if request.method == 'POST':
        otp_input = request.form['otp']

        # Check OTP expiry
        if time.time() - OTP_TIMESTAMP.get(username, 0) > OTP_EXPIRY:
            flash("OTP expired. Login again.")
            session.pop('username', None)
            return redirect(url_for('home'))

        attempts += 1
        session['otp_attempts'] = attempts

        if attempts > MAX_ATTEMPTS:
            flash("Maximum OTP attempts exceeded. Login again.")
            sesion.clear()
            return redirect(url_for('home'))

        if otp_input == CURRENT_OTP.get(username):
            session.pop('username', None)
            session.pop('otp_attempts', None)
            flash("✅ Login successful! 2FA verified.")
            return render_template("success.html",username=username)
        else:
            flash(f"Invalid OTP! Attempts left: {MAX_ATTEMPTS - attempts}")
            return redirect(url_for('two_factor'))

    return render_template('otp.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
