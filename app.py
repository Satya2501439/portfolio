import os

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Allow requests from the portfolio HTML file

MJ_API_KEY = os.environ.get('MJ_API_KEY', '').strip()
MJ_SECRET_KEY = os.environ.get('MJ_SECRET_KEY', '').strip()
MJ_SENDER = os.environ.get('MJ_SENDER', '').strip()
MJ_RECEIVER = os.environ.get('MJ_RECEIVER', '').strip()
MJ_NAME = os.environ.get('MJ_NAME', 'Satya').strip() or 'Satya'


def missing_mailjet_settings():
    required = {
        'MJ_API_KEY': MJ_API_KEY,
        'MJ_SECRET_KEY': MJ_SECRET_KEY,
        'MJ_SENDER': MJ_SENDER,
        'MJ_RECEIVER': MJ_RECEIVER,
    }
    return [name for name, value in required.items() if not value]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_email():
    data = request.get_json(silent=True) or {}

    missing_settings = missing_mailjet_settings()
    if missing_settings:
        return jsonify({
            'error': 'Mail service is not configured',
            'missing': missing_settings,
        }), 500

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({'error': 'Missing required fields'}), 400

    html_body = f"""
    <div style="font-family:monospace;background:#080c10;color:#e2e8f0;padding:2rem;border-radius:8px;max-width:600px;">
      <div style="color:#00e5ff;font-size:0.75rem;letter-spacing:0.1em;margin-bottom:1.5rem;">// NEW MESSAGE FROM PORTFOLIO</div>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#64748b;padding:0.4rem 0;width:90px;">Name</td><td style="color:#e2e8f0;">{name}</td></tr>
        <tr><td style="color:#64748b;padding:0.4rem 0;">Email</td><td style="color:#00e5ff;">{email}</td></tr>
        <tr><td style="color:#64748b;padding:0.4rem 0;">Subject</td><td style="color:#e2e8f0;">{subject or '-'}</td></tr>
      </table>
      <hr style="border:none;border-top:1px solid #1e2d3d;margin:1.25rem 0;"/>
      <div style="color:#64748b;font-size:0.7rem;letter-spacing:0.1em;margin-bottom:0.75rem;">// MESSAGE</div>
      <p style="color:#e2e8f0;line-height:1.8;white-space:pre-wrap;">{message}</p>
    </div>
    """

    payload = {
        'Messages': [{
            'From': {'Email': MJ_SENDER, 'Name': f"{MJ_NAME}'s Portfolio"},
            'To': [{'Email': MJ_RECEIVER, 'Name': MJ_NAME}],
            'ReplyTo': {'Email': email, 'Name': name},
            'Subject': f"[Portfolio] {subject}" if subject else f"[Portfolio] New message from {name}",
            'HTMLPart': html_body,
            'TextPart': f"Name: {name}\nEmail: {email}\nSubject: {subject or '-'}\n\n{message}"
        }]
    }

    try:
        res = requests.post(
            'https://api.mailjet.com/v3.1/send',
            auth=(MJ_API_KEY, MJ_SECRET_KEY),
            json=payload,
            timeout=20,
        )

        result = res.json()
        status = result.get('Messages', [{}])[0].get('Status', '')

        if res.status_code == 200 and status == 'success':
            return jsonify({'success': True}), 200

        print('Mailjet error:', result)
        return jsonify({'error': 'Mailjet rejected the request', 'detail': result}), 500

    except requests.RequestException as exc:
        print('Request exception:', exc)
        return jsonify({'error': 'Failed to reach Mailjet', 'detail': str(exc)}), 502
    except Exception as exc:
        print('Exception:', exc)
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    print('Portfolio mail server running at http://localhost:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)