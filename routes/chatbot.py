from flask import Blueprint, request, jsonify
from services.openrouter import get_chatbot_response

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    response = get_chatbot_response(message)
    return jsonify({'response': response})
