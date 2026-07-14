from datetime import datetime
from . import db


class Category(db.Model):
    __tablename__ = 'categories'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon        = db.Column(db.String(50), default='fa-book')
    color       = db.Column(db.String(20), default='#6366f1')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    books = db.relationship('Book', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Book(db.Model):
    __tablename__ = 'books'

    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(300), nullable=False)
    author           = db.Column(db.String(200), nullable=False)
    isbn             = db.Column(db.String(20), unique=True, nullable=True)
    publisher        = db.Column(db.String(150))
    published_year   = db.Column(db.Integer)
    description      = db.Column(db.Text)
    language         = db.Column(db.String(50), default='English')
    pages            = db.Column(db.Integer)
    category_id      = db.Column(db.Integer, db.ForeignKey('categories.id'))

    # Physical copies
    copies_total     = db.Column(db.Integer, default=1)
    copies_available = db.Column(db.Integer, default=1)
    location         = db.Column(db.String(100))  # shelf/rack location

    # Cover
    cover_image      = db.Column(db.String(500), default='')

    # Ebook / PDF
    has_ebook        = db.Column(db.Boolean, default=False)
    pdf_file         = db.Column(db.String(300))  # local upload path

    # Metadata
    tags             = db.Column(db.String(500))  # comma-separated
    rating           = db.Column(db.Float, default=0.0)
    times_borrowed   = db.Column(db.Integer, default=0)
    added_by         = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    borrow_records   = db.relationship('BorrowRecord',    backref='book', lazy='dynamic')
    reservations     = db.relationship('Reservation',     backref='book', lazy='dynamic')
    wishlist_entries = db.relationship('Wishlist',        backref='book', lazy='dynamic')
    reading_progress = db.relationship('ReadingProgress', backref='book', lazy='dynamic')

    @property
    def is_available(self):
        return self.copies_available > 0

    @property
    def cover_url(self):
        if self.cover_image:
            return f'/static/uploads/covers/{self.cover_image}'
        return '/static/images/default_book.png'

    def __repr__(self):
        return f'<Book {self.title}>'
