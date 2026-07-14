from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models so Flask-Migrate can detect them
from .user     import User
from .book     import Book, Category
from .borrow   import BorrowRecord
from .reservation import Reservation
from .fine     import Fine
from .notification import Notification
from .wishlist import Wishlist
from .reading_progress import ReadingProgress
from .annotation import Annotation
