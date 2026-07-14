from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.book import Book, Category
from models.borrow import BorrowRecord
from models.user import User
from models.notification import Notification
from models.notification import Notification

teacher_bp = Blueprint('teacher', __name__)


def teacher_only(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('teacher', 'admin'):
            flash('Teacher access only.', 'danger')
            return redirect(url_for('landing.index'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ───────────────────────────────────────────────
@teacher_bp.route('/dashboard')
@login_required
@teacher_only
def dashboard():
    # Teacher sees pending borrow requests to approve
    pending_requests = (BorrowRecord.query
                        .filter_by(status='requested')
                        .order_by(BorrowRecord.created_at.desc())
                        .limit(10).all())

    # Books added by this teacher
    my_books = (Book.query
                .filter_by(added_by=current_user.id)
                .order_by(Book.created_at.desc())
                .limit(5).all())

    # Active borrows across all students
    active_borrows = BorrowRecord.query.filter_by(status='borrowed').count()
    overdue_borrows = [r for r in BorrowRecord.query.filter_by(status='borrowed').all() if r.is_overdue]

    student_count = User.query.filter_by(role='student', is_active=True).count()

    return render_template('teacher/dashboard.html',
                           pending_requests=pending_requests,
                           my_books=my_books,
                           active_borrows=active_borrows,
                           overdue_borrows=overdue_borrows,
                           student_count=student_count)


# ─── Approve/Reject Requests ─────────────────────────────────
@teacher_bp.route('/requests')
@login_required
@teacher_only
def requests():
    status = request.args.get('status', 'requested')
    page   = request.args.get('page', 1, type=int)
    records = (BorrowRecord.query
               .filter_by(status=status)
               .order_by(BorrowRecord.created_at.desc())
               .paginate(page=page, per_page=20, error_out=False))
    return render_template('teacher/requests.html', records=records, status=status)


@teacher_bp.route('/requests/<int:rid>/approve', methods=['POST'])
@login_required
@teacher_only
def approve_request(rid):
    record = BorrowRecord.query.get_or_404(rid)
    if record.status != 'requested':
        flash('Already processed.', 'warning')
        return redirect(url_for('teacher.requests'))
    if record.book.copies_available < 1:
        flash('No copies available.', 'danger')
        return redirect(url_for('teacher.requests'))

    record.status = 'borrowed'
    record.approved_by = current_user.id
    record.borrow_date = datetime.utcnow()
    record.set_due_date()
    record.book.copies_available -= 1

    _notify(record.user_id, 'Borrow Approved ✅',
            f'Your request for "{record.book.title}" approved. Due: {record.due_date.strftime("%d %b %Y")}',
            'success')
    db.session.commit()
    flash('Request approved.', 'success')
    return redirect(url_for('teacher.requests'))


@teacher_bp.route('/requests/<int:rid>/reject', methods=['POST'])
@login_required
@teacher_only
def reject_request(rid):
    record = BorrowRecord.query.get_or_404(rid)
    record.status = 'rejected'
    _notify(record.user_id, 'Request Rejected', f'Your request for "{record.book.title}" was rejected.', 'danger')
    db.session.commit()
    flash('Request rejected.', 'info')
    return redirect(url_for('teacher.requests'))


# ─── Upload / Add Book ───────────────────────────────────────
@teacher_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
@teacher_only
def add_book():
    if request.method == 'POST':
        category_id = request.form.get('category_id') or None
        
        import os
        import uuid
        from werkzeug.utils import secure_filename
        from flask import current_app
        
        cover_filename = ''
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename:
            ext = cover_file.filename.rsplit('.', 1)[-1].lower() if '.' in cover_file.filename else 'png'
            cover_filename = f"{uuid.uuid4().hex}.{ext}"
            cover_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'covers')
            os.makedirs(cover_path, exist_ok=True)
            cover_file.save(os.path.join(cover_path, cover_filename))
            
        pdf_filename = ''
        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename:
            ext = pdf_file.filename.rsplit('.', 1)[-1].lower() if '.' in pdf_file.filename else 'pdf'
            pdf_filename = f"{uuid.uuid4().hex}.{ext}"
            pdf_path = current_app.config['EBOOK_FOLDER']
            os.makedirs(pdf_path, exist_ok=True)
            pdf_file.save(os.path.join(pdf_path, pdf_filename))

        book = Book(
            title=request.form['title'],
            author=request.form['author'],
            isbn=request.form.get('isbn') or None,
            publisher=request.form.get('publisher', ''),
            description=request.form.get('description', ''),
            language=request.form.get('language', 'English'),
            category_id=category_id,
            copies_total=int(request.form.get('copies_total', 1)),
            copies_available=int(request.form.get('copies_total', 1)),
            cover_image=cover_filename,
            has_ebook=bool(pdf_filename),
            pdf_file=pdf_filename,
            tags=request.form.get('tags', ''),
            added_by=current_user.id,
        )
        db.session.add(book)
        db.session.commit()
        flash(f'Book "{book.title}" added.', 'success')
        return redirect(url_for('teacher.my_books'))
    categories = Category.query.all()
    return render_template('teacher/add_book.html', categories=categories)


@teacher_bp.route('/books')
@login_required
@teacher_only
def my_books():
    page = request.args.get('page', 1, type=int)
    books = (Book.query
             .filter_by(added_by=current_user.id)
             .order_by(Book.created_at.desc())
             .paginate(page=page, per_page=15, error_out=False))
    return render_template('teacher/my_books.html', books=books)


# ─── Search Books (Local Catalog) ────────────────────────────
@teacher_bp.route('/search')
@login_required
@teacher_only
def search_books():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Book.query
    if q:
        query = query.filter(
            (Book.title.ilike(f'%{q}%')) |
            (Book.author.ilike(f'%{q}%')) |
            (Book.isbn.ilike(f'%{q}%'))
        )
    books = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('teacher/search.html', books=books, q=q, total=books.total)



# ─── Student History (read-only) ─────────────────────────────
@teacher_bp.route('/students')
@login_required
@teacher_only
def students():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    query = User.query.filter_by(role='student')
    if q:
        query = query.filter(
            (User.username.ilike(f'%{q}%')) | (User.full_name.ilike(f'%{q}%'))
        )
    students_page = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('teacher/students.html', students=students_page, q=q)


@teacher_bp.route('/students/<int:uid>/history')
@login_required
@teacher_only
def student_history(uid):
    student = User.query.get_or_404(uid)
    records = (BorrowRecord.query
               .filter_by(user_id=uid)
               .order_by(BorrowRecord.created_at.desc()).all())
    return render_template('teacher/student_history.html', student=student, records=records)





# ─── Profile ─────────────────────────────────────────────────
@teacher_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@teacher_only
def profile():
    if request.method == 'POST':
        current_user.full_name  = request.form.get('full_name', current_user.full_name)
        current_user.phone      = request.form.get('phone', current_user.phone)
        current_user.department = request.form.get('department', current_user.department)
        current_user.bio        = request.form.get('bio', current_user.bio)
        new_pass = request.form.get('new_password')
        if new_pass and len(new_pass) >= 6:
            current_user.set_password(new_pass)
        db.session.commit()
        flash('Profile updated.', 'success')
    return render_template('teacher/profile.html')


def _notify(user_id, title, message, type_='info', link=None):
    n = Notification(user_id=user_id, title=title, message=message, type=type_, link=link)
    db.session.add(n)
