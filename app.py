from flask import Flask, request, session, render_template, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from services.billing import BillingService
from services.print_server import PrintService
import logging
from datetime import datetime
import os

#init flask app
app = Flask(__name__)
app.config.from_object('config.config.Config')
limiter = Limiter(app, key_func=get_remote_address)
billing_service = BillingService()
print_service = PrintService()

if not os.path.exists('logs'):
    os.makedirs('logs')

#logs setup
logging.basicConfig(
    filename='logs/cafe.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)

def authenticate_user(email,password):
    try:
        if email == "test@example.com" and password == "password":
            return {"id": 1, "email": email}
        return None
    except Exception as e:
        logging.error(f"Authentication error: {e}")
        return None

def create_session(user_id):
    try:
        session_id = str(datetime.now().timestamp())
        return session_id
    except Exception as e:
        logging.error(f"Session creation error: {e}")
        return None

def log_activity(user_id, action, ip_address):
    try:
        logging.info(f"User {user_id} performed {action} from {ip_address}")
    except Exception as e:
        logging.error(f"Activity loggin error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.json
    try:
        user = authenticate_user(data['email'], data['password'])
        if user:
           session['user_id'] = user['id']
           log_activity(user['id'], 'login', request.remote_addr)
           return jsonify({'status': 'success'})
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/start_session', methods=['POST'])
def start_session():
    if 'user_id' not in session:
       return jsonify({'error': 'Not authenticated'}), 401

    try:
        session_id = create_session(session['user_id'])
        return jsonify({'session_id': session_id})
    except Exception as e:
        logging.error(f"Session start error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('end_session', methods=['POST'])
def end_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 402

    try:
        log_activity(session['user_id'], 'end_session', request.remote_addr)
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.erro(f"Session end error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/print', methods=['POST'])
def print_document():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        file = request.files['file']
        printer = request.form.get('printer')

        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)

        job_id = print_service.submit_print_job(
            session['user_id'],
            temp_path,
            printer
        )

        if job_id:
            return jsonify({'job_id': job_id})
        return jsonify({'error': 'Print failed'}), 500
    except Exception as e:
        logging.error(f"Print error: {e}")
        return jsonify({'error': 'Server error'}), 500
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('get_balance', methods=['Get'])
def get_balance():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        balance = billing_service.get_balance(session['user_id'])
        return jsonify({'balance': balance})
    except Exception as e:
        logging.error(f"Balance check error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/add_credit,', methdos=['POST'])
def add_credit():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        amount = float(request.json['amount'])
        if billing_service.add_credit(session['user_id'], amount):
            log_activity(session['user_id'], f'add_credit_{amount}', request.remote_addr)
            return jsonify({'status': 'success'})
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Add credit error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    try:
        if 'user_id' in session:
            log_activity(session['user_id'], 'logout', request.remote_addr)
            session.clear()
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Logout error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def internal_error(e):
    logging.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':

    app.secret_key = os.urandom(24) 

    if not os.path.exists('logs'):
        os.makedirs('logs')

app.run(host = '0.0.0.0', port = 5000, ssl_context = 'adhoc')
