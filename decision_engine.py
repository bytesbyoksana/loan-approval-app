import json
from datetime import datetime
from typing import Dict, Any, Tuple


class DecisionEngine:
    def __init__(self, rules_path: str = 'rules.json', messages_path: str = 'messages.json'):
        with open(rules_path, 'r') as f:
            self.rules = json.load(f)
        with open(messages_path, 'r') as f:
            self.messages = json.load(f)
    
    def evaluate_application(self, application: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Evaluate loan application and return decision with message.
        Returns: (decision_type, message_data)
        """
        # Validate compliance first
        compliance_check = self._check_compliance(application)
        if not compliance_check['valid']:
            return 'denied_compliance', self._format_message('denied_compliance', application)
        
        # Extract application data
        credit_score = application['credit_score']
        loan_amount = application['loan_amount']
        annual_income = application['annual_income']
        has_bankruptcy = application['has_bankruptcy']
        
        # Calculate loan-to-income ratio
        loan_to_income = loan_amount / annual_income if annual_income > 0 else float('inf')
        
        # Decision logic
        decision = self._make_decision(credit_score, loan_to_income, has_bankruptcy)
        
        # Format and return message
        message_data = self._format_message(decision, application)
        message_data['loan_to_income_ratio'] = round(loan_to_income, 2)
        
        return decision, message_data
    
    def _check_compliance(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Check if application meets compliance requirements."""
        compliance = self.rules['compliance']
        
        # Check required fields
        for field in compliance['required_fields']:
            if field not in application or application[field] is None:
                return {'valid': False, 'reason': f'Missing required field: {field}'}
        
        # Check credit score range
        credit_score = application.get('credit_score', 0)
        if credit_score < compliance['minimum_credit_score']:
            return {'valid': False, 'reason': 'Credit score below minimum'}
        
        # Check maximum loan amount
        loan_amount = application.get('loan_amount', 0)
        if loan_amount > compliance['maximum_loan_amount']:
            return {'valid': False, 'reason': 'Loan amount exceeds maximum'}
        
        return {'valid': True}
    
    def _make_decision(self, credit_score: int, loan_to_income: float, has_bankruptcy: bool) -> str:
        """Apply decision matrix to determine approval status."""
        brackets = self.rules['credit_score_brackets']
        
        # Pre-approved criteria - excellent credit, no bankruptcy, reasonable ratio
        if (credit_score >= brackets['pre_approved_min'] and 
            not has_bankruptcy and 
            loan_to_income <= self.rules['loan_to_income_ratio']['max_ratio']):
            return 'pre_approved'
        
        # Conditional - excellent credit but bankruptcy
        if credit_score >= brackets['pre_approved_min'] and has_bankruptcy:
            return 'conditional'
        
        # Conditional - excellent credit but high loan-to-income (needs agent review)
        if credit_score >= brackets['pre_approved_min'] and loan_to_income > self.rules['loan_to_income_ratio']['max_ratio']:
            return 'conditional'
        
        # Conditional - moderate credit
        if (brackets['conditional_min'] <= credit_score < brackets['pre_approved_min'] and 
            loan_to_income <= 0.5):
            return 'conditional'
        
        # Denied - low credit or excessive loan-to-income
        return 'denied'
    
    def _format_message(self, decision: str, application: Dict[str, Any]) -> Dict[str, Any]:
        """Format human-friendly message based on decision."""
        message_template = self.messages['decisions'].get(decision, self.messages['decisions']['denied'])
        
        # Replace placeholders
        formatted_message = {
            'decision': decision,
            'title': message_template['title'],
            'message': message_template['message'].replace(
                '${loan_amount}', 
                f"${application.get('loan_amount', 0):,.2f}"
            ),
            'next_steps': message_template['next_steps']
        }
        
        return formatted_message
    
    def get_error_message(self, error_key: str) -> str:
        """Get error message by key."""
        return self.messages['errors'].get(error_key, self.messages['errors']['system_error'])
    
    def get_contact_message(self, preference: str, email: str) -> Dict[str, str]:
        """Get contact preference confirmation message."""
        pref_key = 'yes' if preference.lower() == 'yes' else 'no'
        message_template = self.messages['contact_preference'][pref_key]
        
        return {
            'title': message_template['title'],
            'message': message_template['message'].replace('{email}', email)
        }
