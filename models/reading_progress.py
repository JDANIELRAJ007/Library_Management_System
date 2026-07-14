from datetime import datetime
from . import db


class ReadingProgress(db.Model):
    __tablename__ = 'reading_progress'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id      = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    current_page = db.Column(db.Integer, default=0)
    total_pages  = db.Column(db.Integer, default=0)
    percent      = db.Column(db.Float, default=0.0)
    last_read    = db.Column(db.DateTime, default=datetime.utcnow)
    completed    = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_progress'),)

    def __repr__(self):
        return f'<ReadingProgress user={self.user_id} book={self.book_id} page={self.current_page}>'
