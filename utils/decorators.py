from flask_login import LoginManager
from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


def role_required(*roles):
    """Decorator to restrict access to specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Access denied. You do not have permission to view this page.', 'danger')
                return redirect(url_for('landing.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def teacher_required(f):
    return role_required('teacher', 'admin')(f)
