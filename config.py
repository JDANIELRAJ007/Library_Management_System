import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'edulib-super-secret-2026'
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + os.path.join(basedir, 'database', 'library.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenRouter
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

    # Razorpay
    RAZORPAY_API_KEY = os.environ.get('RAZORPAY_API_KEY', 'rzp_test_TBqfXFmCuY79Zk')
    RAZORPAY_SECRET_KEY = os.environ.get('RAZORPAY_SECRET_KEY', '')

    # Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    EBOOK_FOLDER  = os.path.join(basedir, 'static', 'ebooks')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB

    # Mail (optional – set in .env)
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

    # Fine settings (₹ per day)
    FINE_PER_DAY = 5
    BORROW_DAYS  = 7   # default borrow period
