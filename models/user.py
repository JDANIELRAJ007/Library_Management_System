from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(64),  unique=True, nullable=False, index=True)
    email        = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name    = db.Column(db.String(120))
    role         = db.Column(db.String(20), nullable=False, default='student')
    # role: 'admin' | 'teacher' | 'student'

    phone        = db.Column(db.String(20))
    department   = db.Column(db.String(100))   # for teachers
    student_id   = db.Column(db.String(50))    # for students
    employee_id  = db.Column(db.String(50))    # for teachers/admin
    profile_pic  = db.Column(db.String(200), default='default_avatar.png')
    bio          = db.Column(db.Text)

    is_active    = db.Column(db.Boolean, default=True)
    is_verified  = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_login   = db.Column(db.DateTime)

    # Relationships
    borrow_records  = db.relationship('BorrowRecord',   backref='user', lazy='dynamic',
                                      foreign_keys='BorrowRecord.user_id')
    reservations    = db.relationship('Reservation',    backref='user', lazy='dynamic')
    fines           = db.relationship('Fine',           backref='user', lazy='dynamic')
    notifications   = db.relationship('Notification',  backref='user', lazy='dynamic')
    wishlist        = db.relationship('Wishlist',       backref='user', lazy='dynamic')
    reading_progress = db.relationship('ReadingProgress', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self):
        return self.full_name or self.username

    @property
    def active_borrows(self):
        from .borrow import BorrowRecord
        return self.borrow_records.filter_by(status='borrowed').count()

    @property
    def pending_fines(self):
        from .fine import Fine
        return db.session.query(db.func.sum(Fine.amount)).filter(
            Fine.user_id == self.id, Fine.paid == False
        ).scalar() or 0

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
