from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from models import db
from models.book import Book, Category
from models.borrow import BorrowRecord
from models.fine import Fine
from models.notification import Notification
from models.wishlist import Wishlist
from models.reading_progress import ReadingProgress
from models.reservation import Reservation
from models.annotation import Annotation

student_bp = Blueprint('student', __name__)


def student_only(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('student', 'admin'):
            flash('Student access only.', 'danger')
            return redirect(url_for('landing.index'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ───────────────────────────────────────────────
@student_bp.route('/dashboard')
@login_required
@student_only
def dashboard():
    active_borrows = BorrowRecord.query.filter_by(
        user_id=current_user.id, status='borrowed').all()
    pending_requests = BorrowRecord.query.filter_by(
        user_id=current_user.id, status='requested').all()
    pending = len(pending_requests)
    overdue = [r for r in active_borrows if r.is_overdue]
    unpaid_fines = current_user.pending_fines

    wishlist = (Wishlist.query
                .filter_by(user_id=current_user.id)
                .order_by(Wishlist.added_at.desc())
                .limit(4).all())
    notifications = (Notification.query
                     .filter_by(user_id=current_user.id, is_read=False)
                     .order_by(Notification.created_at.desc())
                     .limit(5).all())
    reading = (ReadingProgress.query
               .filter_by(user_id=current_user.id, completed=False)
               .order_by(ReadingProgress.last_read.desc())
               .limit(4).all())

    # Featured books for the dashboard
    featured_books = Book.query.order_by(Book.times_borrowed.desc()).limit(6).all()
    new_arrivals = Book.query.order_by(Book.created_at.desc()).limit(6).all()

    return render_template('student/dashboard.html',
                           active_borrows=active_borrows,
                           pending=pending,
                           pending_requests=pending_requests,
                           overdue=overdue,
                           unpaid_fines=unpaid_fines,
                           wishlist=wishlist,
                           notifications=notifications,
                           reading=reading,
                           featured_books=featured_books,
                           new_arrivals=new_arrivals)


# ─── Search / Browse Books ──────────────────────────────────
@student_bp.route('/search')
@login_required
@student_only
def search():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', 0, type=int)
    has_ebook = request.args.get('ebook', '')

    query = Book.query
    if q:
        query = query.filter(
            (Book.title.ilike(f'%{q}%')) |
            (Book.author.ilike(f'%{q}%')) |
            (Book.isbn.ilike(f'%{q}%')) |
            (Book.tags.ilike(f'%{q}%'))
        )
    if category_id:
        query = query.filter_by(category_id=category_id)
    if has_ebook == '1':
        query = query.filter_by(has_ebook=True)

    paginated = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    local_books = paginated.items
    total = paginated.total
    categories = Category.query.order_by(Category.name).all()

    return render_template('student/search.html',
                           q=q,
                           local_books=local_books,
                           total=total,
                           page=page,
                           categories=categories,
                           category_id=category_id,
                           has_ebook=has_ebook,
                           paginated=paginated)


# ─── Book Detail ─────────────────────────────────────────────
@student_bp.route('/book/<int:bid>')
@login_required
@student_only
def book_detail(bid):
    book = Book.query.get_or_404(bid)
    in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, book_id=bid).first() is not None
    active_borrow = BorrowRecord.query.filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.book_id == bid,
        BorrowRecord.status.in_(['requested', 'borrowed'])
    ).first()
    return render_template('student/book_detail.html', book=book,
                           in_wishlist=in_wishlist, active_borrow=active_borrow)


# ─── Read E-Book ─────────────────────────────────────────────
@student_bp.route('/read/<int:bid>')
@login_required
def read_ebook(bid):
    book = Book.query.get_or_404(bid)
    if not book.has_ebook or not book.pdf_file:
        flash('E-book not available for this title.', 'danger')
        return redirect(request.referrer or url_for('student.search'))
    annotation = Annotation.query.filter_by(user_id=current_user.id, book_id=bid).first()
    return render_template('student/ebook_reader.html', book=book, annotation=annotation)

@student_bp.route('/read/<int:bid>/save_annotation', methods=['POST'])
@login_required
def save_annotation(bid):
    content = request.form.get('content', '')
    annotation = Annotation.query.filter_by(user_id=current_user.id, book_id=bid).first()
    if annotation:
        annotation.content = content
    else:
        annotation = Annotation(user_id=current_user.id, book_id=bid, content=content)
        db.session.add(annotation)
    db.session.commit()
    flash('Notes saved successfully!', 'success')
    return redirect(url_for('student.read_ebook', bid=bid))



# ─── Borrow Request ──────────────────────────────────────────
@student_bp.route('/borrow/<int:bid>', methods=['POST'])
@login_required
@student_only
def borrow_book(bid):
    book = Book.query.get_or_404(bid)
    existing = BorrowRecord.query.filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.book_id == bid,
        BorrowRecord.status.in_(['requested', 'borrowed'])
    ).first()
    if existing:
        flash('You already have an active request or borrow for this book.', 'warning')
        return redirect(request.referrer or url_for('student.search'))

    if book.copies_available < 1:
        r = Reservation(user_id=current_user.id, book_id=bid)
        db.session.add(r)
        db.session.commit()
        flash(f'No copies available. "{book.title}" added to your reservations.', 'info')
        return redirect(request.referrer or url_for('student.search'))

    record = BorrowRecord(user_id=current_user.id, book_id=bid, status='requested')
    db.session.add(record)
    db.session.commit()
    flash(f'Borrow request for "{book.title}" submitted! Awaiting approval.', 'success')
    return redirect(url_for('student.dashboard'))


# ─── Return Book ─────────────────────────────────────────────
@student_bp.route('/return/<int:rid>', methods=['POST'])
@login_required
@student_only
def return_book(rid):
    record = BorrowRecord.query.get_or_404(rid)
    if record.user_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('student.dashboard'))
    flash('Please return the book to the library counter. Admin will mark it returned.', 'info')
    return redirect(url_for('student.dashboard'))


# ─── Wishlist ─────────────────────────────────────────────────
@student_bp.route('/wishlist/toggle/<int:bid>', methods=['POST'])
@login_required
@student_only
def toggle_wishlist(bid):
    book = Book.query.get_or_404(bid)
    existing = Wishlist.query.filter_by(user_id=current_user.id, book_id=bid).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash(f'Removed "{book.title}" from wishlist.', 'info')
    else:
        w = Wishlist(user_id=current_user.id, book_id=bid)
        db.session.add(w)
        db.session.commit()
        flash(f'Added "{book.title}" to wishlist! ❤️', 'success')
    return redirect(request.referrer or url_for('student.wishlist'))


@student_bp.route('/wishlist')
@login_required
@student_only
def wishlist():
    items = (Wishlist.query
             .filter_by(user_id=current_user.id)
             .order_by(Wishlist.added_at.desc()).all())
    return render_template('student/wishlist.html', items=items)


# ─── Notifications ───────────────────────────────────────────
@student_bp.route('/notifications')
@login_required
@student_only
def notifications():
    notifs = (Notification.query
              .filter_by(user_id=current_user.id)
              .order_by(Notification.created_at.desc())
              .all())
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('student/notifications.html', notifications=notifs)


# ─── Borrow History ──────────────────────────────────────────
@student_bp.route('/history')
@login_required
@student_only
def history():
    page = request.args.get('page', 1, type=int)
    records = (BorrowRecord.query
               .filter_by(user_id=current_user.id)
               .order_by(BorrowRecord.created_at.desc())
               .paginate(page=page, per_page=15, error_out=False))
    return render_template('student/history.html', records=records)


# ─── Fines ───────────────────────────────────────────────────
@student_bp.route('/fines')
@login_required
@student_only
def fines():
    my_fines = (Fine.query
                .filter_by(user_id=current_user.id)
                .order_by(Fine.created_at.desc()).all())
    razorpay_key = current_app.config.get('RAZORPAY_API_KEY', '')
    return render_template('student/fines.html', fines=my_fines, razorpay_key=razorpay_key)

@student_bp.route('/fines/pay/<int:fid>', methods=['POST'])
@login_required
@student_only
def pay_fine(fid):
    fine = Fine.query.get_or_404(fid)
    if fine.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('student.fines'))
    
    payment_id = request.form.get('razorpay_payment_id')
    if payment_id:
        fine.paid = True
        fine.paid_at = datetime.utcnow()
        fine.razorpay_payment_id = payment_id
        db.session.commit()
        flash('Payment successful via Razorpay!', 'success')
    else:
        flash('Payment failed or cancelled.', 'warning')
    
    return redirect(url_for('student.fines'))


# ─── Profile ─────────────────────────────────────────────────
@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_only
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.bio = request.form.get('bio', current_user.bio)
        new_pass = request.form.get('new_password')
        if new_pass:
            if len(new_pass) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('student.profile'))
            current_user.set_password(new_pass)
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    return render_template('student/profile.html')
