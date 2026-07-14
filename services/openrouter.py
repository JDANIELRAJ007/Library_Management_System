import os
import requests
from flask import current_app


def get_chatbot_response(message, context='library'):
    api_key = current_app.config.get('OPENROUTER_API_KEY', '')
    if not api_key or api_key == 'your_openrouter_api_key_here':
        return "⚠️ AI Librarian is not configured. Please set OPENROUTER_API_KEY in your .env file."

    system_prompt = """You are EduLib AI, an intelligent library assistant for a university library management system.
You help students, teachers, and librarians with:
- Book recommendations based on topics, interests, or courses
- Explaining academic concepts in simple terms
- Library policies (borrowing, fines, reservations)
- Research guidance and study tips
- Finding books by author, genre, ISBN, or subject
- Summarizing book topics

Keep responses concise, helpful, and educational. Use emojis sparingly for clarity."""

    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'EduLib AI Librarian',
    }
    payload = {
        'model': 'openrouter/free',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': message},
        ],
        'max_tokens': 600,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        current_app.logger.error(f'OpenRouter error: {e}')
        return "Sorry, I'm having trouble connecting right now. Please try again later."
