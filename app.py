from flask import Flask, render_template, request, jsonify
import json
import re
import bleach
from datetime import datetime, timedelta
from decision_engine import DecisionEngine

app = Flask(__name__)
engine = DecisionEngine()

SUBMISSIONS_FILE = 'submissions.json'
RESUBMISSION_DAYS = 7  # Days before allowing resubmission


def sanitize_input(text: str) -> str:
    """Sanitize text input to prevent injection."""
    if not isinstance(text, str):
        return str(text)
    return bleach.clean(text.strip())


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def check_existing_submission(email: str):
    """Check if email has recent submission. Returns (exists, days_remaining, old_submission)."""
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            submissions = json.load(f)
        
        for submission in reversed(submissions):
            if submission.get('email', '').lower() == email.lower():
                submission_date = datetime.fromisoformat(submission['timestamp'])
                days_since = (datetime.now() - submission_date).days
                
                if days_since < RESUBMISSION_DAYS:
                    days_remaining = RESUBMISSION_DAYS - days_since
                    return True, days_remaining, submission
                else:
                    return False, 0, submission
        
        return False, 0, None
    except FileNotFoundError:
        return False, 0, None


def save_submission(data: dict):
    """Save submission to JSON file."""
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            submissions = json.load(f)
    except FileNotFoundError:
        submissions = []
    
    # Check if updating existing submission
    email = data['email'].lower()
    updated = False
    for i, sub in enumerate(submissions):
        if sub.get('email', '').lower() == email:
            submission_date = datetime.fromisoformat(sub['timestamp'])
            if (datetime.now() - submission_date).days >= RESUBMISSION_DAYS:
                submissions[i] = data
                updated = True
                break
    
    if not updated:
        submissions.append(data)
    
    with open(SUBMISSIONS_FILE, 'w') as f:
        json.dump(submissions, f, indent=2)


@app.route('/')
def index():
    """Render user-facing form."""
    return render_template('form.html')


@app.route('/submit', methods=['POST'])
def submit_application():
    """Handle form submission from user."""
    # Extract and sanitize form data
    name = sanitize_input(request.form.get('name', ''))
    email = sanitize_input(request.form.get('email', ''))
    loan_amount = request.form.get('loan_amount', '0')
    credit_score = request.form.get('credit_score', '0')
    annual_income = request.form.get('annual_income', '0')
    has_bankruptcy = request.form.get('has_bankruptcy', 'no')
    
    # Validation - stay on page for errors
    if not name or not email:
        return render_template('form.html', 
                               error=engine.get_error_message('missing_fields'),
                               name=name, email=email, loan_amount=loan_amount,
                               annual_income=annual_income, credit_score=credit_score,
                               has_bankruptcy=has_bankruptcy)
    
    if not validate_email(email):
        return render_template('form.html', 
                               error=engine.get_error_message('invalid_email'),
                               name=name, email=email, loan_amount=loan_amount,
                               annual_income=annual_income, credit_score=credit_score,
                               has_bankruptcy=has_bankruptcy)
    
    # Check for existing submission
    exists, days_remaining, old_sub = check_existing_submission(email)
    if exists:
        error_msg = f"You have already submitted an application. You can resubmit in {days_remaining} day{'s' if days_remaining != 1 else ''}."
        return render_template('form.html',
                               error=error_msg,
                               name=name, email=email, loan_amount=loan_amount,
                               annual_income=annual_income, credit_score=credit_score,
                               has_bankruptcy=has_bankruptcy)
    
    try:
        loan_amount = float(loan_amount)
        credit_score = int(credit_score)
        annual_income = float(annual_income)
        has_bankruptcy = (has_bankruptcy == 'yes')
    except ValueError:
        return render_template('form.html', 
                               error=engine.get_error_message('system_error'),
                               name=name, email=email)
    
    # Additional validation
    if not (300 <= credit_score <= 850):
        return render_template('form.html', 
                               error=engine.get_error_message('invalid_credit_score'),
                               name=name, email=email, loan_amount=loan_amount,
                               annual_income=annual_income, credit_score=credit_score,
                               has_bankruptcy='yes' if has_bankruptcy else 'no')
    
    if loan_amount <= 0:
        return render_template('form.html', 
                               error=engine.get_error_message('invalid_loan_amount'),
                               name=name, email=email, loan_amount=loan_amount,
                               annual_income=annual_income, credit_score=credit_score,
                               has_bankruptcy='yes' if has_bankruptcy else 'no')
    
    if annual_income <= 0:
        return render_template('form.html', 
                               error=engine.get_error_message('invalid_income'),
                               name=name, email=email, loan_amount=loan_amount,
                               annual_income=annual_income, credit_score=credit_score,
                               has_bankruptcy='yes' if has_bankruptcy else 'no')
    
    # Build application object
    application = {
        'name': name,
        'email': email,
        'loan_amount': loan_amount,
        'credit_score': credit_score,
        'annual_income': annual_income,
        'has_bankruptcy': has_bankruptcy,
        'timestamp': datetime.now().isoformat()
    }
    
    # Evaluate application
    decision, message_data = engine.evaluate_application(application)
    
    # Save submission
    submission_record = {
        **application,
        'decision': decision,
        'contact_requested': None
    }
    save_submission(submission_record)
    
    return render_template('result.html', 
                           decision=message_data,
                           application=application)


@app.route('/contact', methods=['POST'])
def contact_preference():
    """Handle contact preference."""
    preference = request.form.get('preference', 'no')
    email = sanitize_input(request.form.get('email', ''))
    
    # Update last submission with contact preference
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            submissions = json.load(f)
        
        # Find and update the submission for this email
        for submission in reversed(submissions):
            if submission.get('email', '').lower() == email.lower():
                submission['contact_requested'] = (preference == 'yes')
                submission['contact_timestamp'] = datetime.now().isoformat()
                break
        
        with open(SUBMISSIONS_FILE, 'w') as f:
            json.dump(submissions, f, indent=2)
    except Exception:
        pass
    
    message = engine.get_contact_message(preference, email)
    return render_template('result.html', contact_message=message)


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """API endpoint for programmatic testing with JSON input."""
    try:
        application = request.get_json()
        
        # Validate required fields
        required = ['name', 'email', 'loan_amount', 'credit_score', 'annual_income', 'has_bankruptcy']
        for field in required:
            if field not in application:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check for existing submission
        exists, days_remaining, old_sub = check_existing_submission(application['email'])
        if exists:
            return jsonify({
                'error': f'Email already submitted. Resubmission allowed in {days_remaining} days.',
                'existing_submission': old_sub
            }), 409
        
        # Add timestamp
        application['timestamp'] = datetime.now().isoformat()
        
        # Evaluate
        decision, message_data = engine.evaluate_application(application)
        
        # Save submission
        submission_record = {
            **application,
            'decision': decision,
            'source': 'api'
        }
        save_submission(submission_record)
        
        return jsonify({
            'success': True,
            'decision': decision,
            'message': message_data,
            'application': application
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions (for programmatic review)."""
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            submissions = json.load(f)
        return jsonify({'submissions': submissions})
    except FileNotFoundError:
        return jsonify({'submissions': []})


if __name__ == '__main__':
    # Initialize submissions file if it doesn't exist
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            pass
    except FileNotFoundError:
        with open(SUBMISSIONS_FILE, 'w') as f:
            json.dump([], f)
    
    app.run(debug=True, port=5000)
