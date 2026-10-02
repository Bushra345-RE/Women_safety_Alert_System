from flask import Blueprint, request, jsonify, session
from models import db, User, Alert
from werkzeug.security import generate_password_hash, check_password_hash
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

api = Blueprint('api', __name__)

TWILIO_SID      = os.environ.get('TWILIO_SID', '')
TWILIO_AUTH     = os.environ.get('TWILIO_AUTH', '')
TWILIO_PHONE    = os.environ.get('TWILIO_PHONE', '')
TWILIO_WA_PHONE = os.environ.get('TWILIO_WA_PHONE', '')
GMAIL_USER      = os.environ.get('GMAIL_USER', '')
GMAIL_PASSWORD  = os.environ.get('GMAIL_PASSWORD', '')


def send_sms(to_number, message):
    try:
        from twilio.rest import Client
        if not TWILIO_SID or not TWILIO_AUTH or not TWILIO_PHONE:
            print('⚠️  Twilio SMS not configured')
            return False
        client = Client(TWILIO_SID, TWILIO_AUTH)
        client.messages.create(body=message, from_=TWILIO_PHONE, to=to_number)
        print(f'✅ SMS sent to {to_number}')
        return True
    except Exception as e:
        print(f'❌ SMS failed: {e}')
        return False


def send_whatsapp(to_number, message):
    try:
        from twilio.rest import Client
        if not TWILIO_SID or not TWILIO_AUTH or not TWILIO_WA_PHONE:
            print('⚠️  Twilio WhatsApp not configured')
            return False
        client = Client(TWILIO_SID, TWILIO_AUTH)
        wa_to = f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number
        client.messages.create(body=message, from_=TWILIO_WA_PHONE, to=wa_to)
        print(f'✅ WhatsApp sent to {to_number}')
        return True
    except Exception as e:
        print(f'❌ WhatsApp failed: {e}')
        return False


def send_email(to_email, subject, html_body):
    try:
        if not GMAIL_USER or not GMAIL_PASSWORD:
            print('⚠️  Gmail not configured')
            return False
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'SHEild Safety <{GMAIL_USER}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        print(f'✅ Email sent to {to_email}')
        return True
    except Exception as e:
        print(f'❌ Email failed: {e}')
        return False


def build_message(user_name, lat, lng, address, alert_time):
    maps_url = f'https://www.google.com/maps?q={lat},{lng}'
    return (
        f'🚨 SOS ALERT from {user_name}!\n'
        f'📍 Location: {address or "See map link"}\n'
        f'🗺 Map: {maps_url}\n'
        f'🕐 Time: {alert_time}\n'
        f'Please respond immediately!'
    )


def build_email_html(user_name, lat, lng, address, alert_time):
    maps_url = f'https://www.google.com/maps?q={lat},{lng}'
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#0a0a0a;font-family:Arial,sans-serif;">
      <div style="max-width:600px;margin:0 auto;padding:32px 24px;">

        <div style="background:linear-gradient(135deg,#dc2626,#7f1d1d);border-radius:16px;
                    padding:32px;text-align:center;margin-bottom:24px;">
          <div style="font-size:56px;margin-bottom:12px;">🚨</div>
          <h1 style="color:#fff;margin:0;font-size:28px;letter-spacing:2px;">SOS ALERT</h1>
          <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;">Emergency Alert from SHEild</p>
        </div>

        <div style="background:#1a1a2e;border:1px solid rgba(220,38,38,0.3);
                    border-left:4px solid #dc2626;border-radius:12px;padding:24px;margin-bottom:20px;">
          <h2 style="color:#ff6b9d;margin:0 0 16px;">⚠️ {user_name} needs help!</h2>
          <table style="width:100%;border-collapse:collapse;">
            <tr>
              <td style="padding:8px 0;color:#888;width:100px;">👤 Name</td>
              <td style="padding:8px 0;color:#fff;font-weight:bold;">{user_name}</td>
            </tr>
            <tr>
              <td style="padding:8px 0;color:#888;">📍 Location</td>
              <td style="padding:8px 0;color:#fff;">{address or 'Location captured'}</td>
            </tr>
            <tr>
              <td style="padding:8px 0;color:#888;">🌐 GPS</td>
              <td style="padding:8px 0;color:#fff;">{lat}, {lng}</td>
            </tr>
            <tr>
              <td style="padding:8px 0;color:#888;">🕐 Time</td>
              <td style="padding:8px 0;color:#fff;">{alert_time}</td>
            </tr>
          </table>
        </div>

        <div style="text-align:center;margin-bottom:24px;">
          <a href="{maps_url}"
             style="display:inline-block;background:linear-gradient(135deg,#dc2626,#7f1d1d);
                    color:#fff;text-decoration:none;padding:16px 40px;
                    border-radius:12px;font-size:16px;font-weight:bold;">
            🗺 Open Live Location
          </a>
        </div>

        <p style="text-align:center;color:#555;font-size:12px;">
          Sent by <strong style="color:#ff2d6e;">SHEild</strong> Women Safety System.
          Please help {user_name} immediately.
        </p>
      </div>
    </body>
    </html>
    """


def notify_contacts(user, lat, lng, address, alert_time):
    contacts = [user.contact1, user.contact2, user.contact3,
                user.contact4, user.contact5]
    contacts = [c.strip() for c in contacts if c and c.strip()]

    if not contacts:
        print('⚠️  No contacts to notify')
        return {'sms': 0, 'whatsapp': 0, 'email': 0}

    message       = build_message(user.name, lat, lng, address, alert_time)
    email_html    = build_email_html(user.name, lat, lng, address, alert_time)
    email_subject = f'🚨 SOS ALERT from {user.name} — Please Help!'

    sms_count = wa_count = email_count = 0

    for contact in contacts:
        if '@' in contact:
            if send_email(contact, email_subject, email_html):
                email_count += 1
        else:
            phone = contact if contact.startswith('+') else '+91' + contact.lstrip('0')
            if send_sms(phone, message):      sms_count += 1
            if send_whatsapp(phone, message): wa_count  += 1

    print(f'📊 Sent — SMS:{sms_count} WhatsApp:{wa_count} Email:{email_count}')
    return {'sms': sms_count, 'whatsapp': wa_count, 'email': email_count}


# ════════════════════════════════
#  ROUTES
# ════════════════════════════════

@api.route('/register', methods=['POST'])
def register():
    d = request.get_json()
    if not d or not all(k in d for k in ('name', 'email', 'password')):
        return jsonify({'error': 'Name, email and password are required'}), 400
    if not d['name'].strip() or not d['email'].strip() or not d['password'].strip():
        return jsonify({'error': 'Fields cannot be empty'}), 400
    if User.query.filter_by(email=d['email'].strip().lower()).first():
        return jsonify({'error': 'Email is already registered'}), 409
    if len(d['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    user = User(
        name     = d['name'].strip(),
        email    = d['email'].strip().lower(),
        password = generate_password_hash(d['password']),
        contact1 = d.get('contact1', '').strip(),
        contact2 = d.get('contact2', '').strip(),
        contact3 = d.get('contact3', '').strip(),
        contact4 = d.get('contact4', '').strip(),
        contact5 = d.get('contact5', '').strip(),
    )
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'message': 'Account created!', 'user': user.to_dict()}), 201


@api.route('/login', methods=['POST'])
def login():
    d = request.get_json()
    if not d or not d.get('email') or not d.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    user = User.query.filter_by(email=d['email'].strip().lower()).first()
    if not user or not check_password_hash(user.password, d['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    session['user_id'] = user.id
    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200


@api.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


@api.route('/sos', methods=['POST'])
def send_sos():
    d = request.get_json()
    if not d:
        return jsonify({'error': 'No data provided'}), 400
    if 'user_id' not in d:
        return jsonify({'error': 'user_id is required'}), 400
    if 'latitude' not in d or 'longitude' not in d:
        return jsonify({'error': 'latitude and longitude are required'}), 400
    user = User.query.get(d['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    alert = Alert(
        user_id   = d['user_id'],
        latitude  = float(d['latitude']),
        longitude = float(d['longitude']),
        address   = d.get('address', '').strip(),
    )
    db.session.add(alert)
    db.session.commit()

    alert_time = alert.time.strftime('%Y-%m-%d %H:%M:%S')
    results = notify_contacts(
        user, d['latitude'], d['longitude'],
        d.get('address', ''), alert_time
    )

    return jsonify({
        'message':       '🚨 SOS Alert sent!',
        'alert':         alert.to_dict(),
        'notifications': results
    }), 201


@api.route('/alerts/<int:user_id>', methods=['GET'])
def get_alerts(user_id):
    alerts = Alert.query.filter_by(user_id=user_id).order_by(Alert.time.desc()).all()
    return jsonify({'alerts': [a.to_dict() for a in alerts], 'count': len(alerts)}), 200


@api.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@api.route('/user/<int:user_id>/contacts', methods=['PUT'])
def update_contacts(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    d = request.get_json() or {}
    user.contact1 = d.get('contact1', user.contact1 or '').strip()
    user.contact2 = d.get('contact2', user.contact2 or '').strip()
    user.contact3 = d.get('contact3', user.contact3 or '').strip()
    user.contact4 = d.get('contact4', user.contact4 or '').strip()
    user.contact5 = d.get('contact5', user.contact5 or '').strip()
    db.session.commit()
    return jsonify({'message': 'Contacts updated', 'user': user.to_dict()}), 200


@api.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'SHEild API is running'}), 200