# EduLib AI-Powered Library Management System

A modern, enterprise-grade AI-powered Library Management System built with Python Flask, SQLAlchemy, HTML5, CSS3, Bootstrap 5, and JavaScript. Features a premium glassmorphism UI, OpenRouter AI Librarian chatbot, and role-based dashboards.

## Features
- **3 User Roles:** Admin, Teacher, Student
- **AI Chatbot:** OpenRouter integration for book recommendations and library queries.
- **Premium UI:** Glassmorphism, animations (AOS), dark/light mode toggle.
- **Authentication:** Secure login, registration with password hashing.

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENROUTER_API_KEY=your_openrouter_api_key
```

3. Initialize the database:
```bash
flask shell
>>> from models import db
>>> db.create_all()
>>> quit()
```

4. Run the application:
```bash
flask run
```
