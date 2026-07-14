from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.openrouter import get_chatbot_response

api_bp = Blueprint('api', __name__)


@api_bp.route('/status')
def status():
    return jsonify({'status': 'ok', 'app': 'EduLib'})


@api_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    response = get_chatbot_response(message)
    return jsonify({'response': response})

@api_bp.route('/ebook/<filename>')
@login_required
def serve_ebook(filename):
    from flask import current_app, send_from_directory
    return send_from_directory(
        current_app.config['EBOOK_FOLDER'],
        filename,
        as_attachment=False
    )


@api_bp.route('/notifications/count')
@login_required
def notification_count():
    from models.notification import Notification
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@api_bp.route('/system-time')
def system_time():
    from datetime import datetime
    return jsonify({
        'system_time': datetime.utcnow().isoformat() + 'Z',
        'formatted': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    })

@api_bp.route('/fine-details')
@login_required
def fine_details():
    from models.fine import Fine
    from models.borrow import BorrowRecord
    
    # Calculate unpaid fines summary for the current user
    unpaid_fines = Fine.query.filter_by(user_id=current_user.id, paid=False).all()
    total_unpaid = sum(f.amount for f in unpaid_fines)
    
    details = []
    for f in unpaid_fines:
        details.append({
            'id': f.id,
            'amount': f.amount,
            'reason': f.reason,
            'date': f.created_at.strftime('%Y-%m-%d')
        })
        
    return jsonify({
        'total_unpaid': total_unpaid,
        'fines': details
    })
