# Loan Pre-Approval Application

This is a prototype application for demonstration purposes.

This sample web application evaluates loan applications and provides instant pre-approval decisions based on credit score, income, loan amount, and bankruptcy history.

## Table of contents

- [Overview](#overview)
- [Target Audience](#target-audience)
- [Features](#features)
- [Decision Logic](#decision-logic)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [How to Launch](#how-to-launch)
- [How to Test](#how-to-test)
- [Security Features](#security-features)
- [Troubleshooting](#troubleshooting)

---

## Overview

This application provides a simple, user-friendly interface for potential borrowers to check their loan pre-approval status. The system evaluates applications based on configurable business rules stored in JSON files, making it easy to update decision criteria without modifying code.

## Target audience

### End users (borrowers)

- Individuals seeking personal loans
- People who want to quickly check their pre-approval status
- Borrowers who prefer online applications over phone calls

### Developers/administrators

- Loan officers who need to test decision logic
- Compliance teams who update approval criteria
- Developers integrating with the decision engine API

---

## Features

### User features

- Responsive web form
- Instant pre-approval decisions
- Human-friendly explanations for all outcomes
- Optional agent contact request
- Mobile-friendly design

### Developer features

- JSON-based testing interface
- REST API for programmatic access
- View all submissions in real-time
- Configurable rules without code changes
- Example test cases included

### Built-in security

- Email format validation
- Input sanitization (prevents injection attacks)
- Credit score range validation (300-850)
- Positive value validation for amounts
- Error handling for malformed data

---

## Decision logic

The application uses a multi-factor decision matrix to evaluate loan applications:

### Credit score brackets

| Credit Score | Base Decision |
|--------------|---------------|
| ≥ 720        | Pre-Approved (if other criteria met) |
| 680-719      | Conditional |
| < 680        | Denied |

### Loan-to-income ratio

- **Pre-Approved**: Loan amount ≤ 40% of annual income
- **Conditional**: Loan amount ≤ 50% of annual income
- **Denied**: Loan amount > 50% of annual income

### Bankruptcy rules

- **Recent bankruptcy + credit ≥ 720**: Conditional (requires agent review)
- **Recent bankruptcy + credit < 720**: Denied
- **No bankruptcy**: Evaluated based on credit score and loan-to-income ratio

### Compliance guardrails

- **Minimum credit score**: 600 (below this = auto-deny)
- **Maximum loan amount**: $500,000 (above this = auto-deny)
- **Required fields**: All form fields must be completed

### Decision outcomes

1. **Pre-Approved**: Excellent credit (≥720), no bankruptcy, reasonable loan-to-income ratio
2. **Conditional**: Good credit (680-719) OR bankruptcy with excellent credit OR needs agent review
3. **Denied**: Low credit (<680), excessive loan-to-income ratio, or compliance violations

---

## Project structure

```text
loan-approval-app/
├── app.py                  # Flask application (main entry point)
├── decision_engine.py      # Core decision logic and evaluation
├── rules.json             # Decision rules and compliance settings
├── messages.json          # Human-friendly messages for all outcomes
├── submissions.json       # Stored application data (auto-generated)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   ├── form.html         # User-facing application form
│   ├── result.html       # Decision result and contact preference
│   └── dev_test.html     # Developer testing interface
└── static/
    └── style.css         # Application styling
```

---

## Setup instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation steps

1. Navigate to the project directory.

1. Create a virtual environment (recommended):

   ```bash
   python3 -m venv venv
   ```

1. Activate the virtual environment:

   **On macOS/Linux:**

   ```bash
   source venv/bin/activate
   ```

   **On Windows:**

   ```bash
   venv\Scripts\activate
   ```

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## How to launch

1. Ensure you're in the project directory with the virtual environment activated.

1. Start the Flask application:

   ```bash
   python app.py
   ```

   You should see the following output:

   ```
   * Running on http://127.0.0.1:5000
   * Debug mode: on
   ```

1. Open your web browser and navigate to:

   ```
   http://127.0.0.1:5000
   ```

---

## How to test

### Option 1: Testing as an end user

1. Ensure Flask is running and `http://127.0.0.1:5000` is open in the browser.

1. Fill out the loan application form with test data.

1. Submit and review the decision.

1. Check stored data by opening `submissions.json` in a text editor.

### Option 2: Testing via API (Command Line)

1. Ensure Flask is running in Terminal 1. For more information, see the earlier section "How to launch."

1. Open a new terminal window (Terminal 2).

1. In Terminal 2, run `curl` commands to test the application. Note: You don't need to activate `venv` in this terminal. Enter the following sample commands. You can change the values for testing purposes.

   **Pre-Approved Example:**

   ```bash
   curl -X POST http://127.0.0.1:5000/api/evaluate \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test User",
       "email": "test@example.com",
       "loan_amount": 50000,
       "credit_score": 750,
       "annual_income": 150000,
       "has_bankruptcy": false
     }'
   ```

   **Conditional Example:**

   ```bash
   curl -X POST http://127.0.0.1:5000/api/evaluate \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Jane Doe",
       "email": "jane@example.com",
       "loan_amount": 30000,
       "credit_score": 690,
       "annual_income": 70000,
       "has_bankruptcy": false
     }'
   ```

   **Denied Example:**

   ```bash
   curl -X POST http://127.0.0.1:5000/api/evaluate \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Bob Smith",
       "email": "bob@example.com",
       "loan_amount": 100000,
       "credit_score": 650,
       "annual_income": 60000,
       "has_bankruptcy": false
     }'
   ```

1. **View all submissions:**

   ```bash
   curl http://127.0.0.1:5000/api/submissions
   ```

---

## Security features

### Input validation

- **Email validation**: Regex pattern matching for valid email format
- **Credit score range**: Must be between 300-850
- **Positive values**: Loan amount and income must be > 0
- **Required fields**: All fields must be completed

### Input sanitization

- **Text sanitization**: Uses `bleach` library to strip HTML/script tags
- **Whitespace trimming**: Removes leading/trailing spaces
- **Type validation**: Ensures numeric fields are proper numbers

### Error handling

- Graceful error messages for invalid input
- Try-catch blocks prevent application crashes
- User-friendly error messages (no technical details exposed)

### Data protection

- No sensitive data logged to console
- JSON storage is local (not exposed via web)
- Email addresses validated before storage

---

## Troubleshooting

### Port already in use

If port 5000 is already in use, modify `app.py`:

```python
app.run(debug=True, port=5001)  # Change to any available port
```

### Module not found errors

Ensure virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Submissions not saving

Check file permissions in the project directory:

```bash
ls -la submissions.json
```

### Browser not loading page

- Verify Flask is running (check terminal output)
- Try `http://localhost:5000` instead of `127.0.0.1`
- Clear browser cache
- Try a different browser
