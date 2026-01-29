from flask import Blueprint, request, jsonify, render_template
import smtplib, ssl, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

verify_bp = Blueprint('verify', __name__, template_folder='templates')

otp_store = {}

def generate_otp():
    """Generate a 6-digit random OTP as a string."""
    return str(random.randint(100000, 999999))

def send_otp_email(receiver_email, otp, sender_email, sender_password):
    """Send an OTP to the specified email address using Gmail SMTP."""
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your OTP Verification Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    html = f"""
    <html>
        <body>
            <p>Hello,<br>
               Your OTP code is: <b>{otp}</b><br>
               This code is valid for a short period.
            </p>
        </body>
    </html>
    """
    part = MIMEText(html, "html")
    message.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print(f"OTP email sent successfully to {receiver_email}")
    except smtplib.SMTPAuthenticationError:
        raise Exception("SMTP Authentication Failed. Check your SENDER_EMAIL and GMAIL_APP_PASSWORD.")
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")

@verify_bp.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400

    otp = generate_otp()
    otp_store[email] = otp

    sender_email = os.environ.get("SENDER_EMAIL", "prernagaur7677@gmail.com")
    sender_password = os.environ.get("GMAIL_APP_PASSWORD", "hqgr ynva njyl ofyi")

    if sender_password == "hqgr ynva njyl ofyi":
        print("\n" + "="*80)
        print("Using default password! Set GMAIL_APP_PASSWORD as an environment variable.")
        print("="*80 + "\n")

    try:
        send_otp_email(email, otp, sender_email, sender_password)
        print(f"Generated OTP for {email}: {otp}")
        return jsonify({'message': 'OTP sent successfully to your email.'}), 200
    except Exception as e:
        import traceback
        print("Error sending OTP:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@verify_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.form.get('email')
        otp = request.form.get('otp')

        if not email or not otp:
            return "Missing email or OTP", 400

        stored_otp = otp_store.get(email)
        if stored_otp and stored_otp == otp:
            otp_store.pop(email, None)
            return '', 200
        elif stored_otp:
            return "Invalid OTP. Please try again.", 401
        else:
            return "No OTP found for this email or it has expired. Please generate a new one.", 404

    return render_template('verify.html')
