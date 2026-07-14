import os
from flask import Flask
from config import Config
from models import db
from utils.decorators import login_manager
from flask_migrate import Migrate

migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EBOOK_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # User loader
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def auto_calculate_fines():
        from flask_login import current_user
        from models.borrow import BorrowRecord
        from models.fine import Fine
        from models.notification import Notification
        
        if current_user.is_authenticated:
            # Check all active borrows so fines are always calculated even when admin is browsing
            active_borrows = BorrowRecord.query.filter_by(status='borrowed').all()
            for record in active_borrows:
                if record.is_overdue:
                    total_fine = record.fine_amount
                    paid_fines = Fine.query.filter_by(borrow_id=record.id, paid=True).all()
                    total_paid = sum(f.amount for f in paid_fines)
                    remaining = total_fine - total_paid
                    
                    unpaid_fine = Fine.query.filter_by(borrow_id=record.id, paid=False).first()
                    
                    if remaining > 0:
                        if not unpaid_fine:
                            fine = Fine(user_id=record.user_id, borrow_id=record.id, amount=remaining, 
                                        reason=f'Overdue fine for "{record.book.title}"')
                            db.session.add(fine)
                            n = Notification(user_id=record.user_id, title='Overdue Alert ⚠️', 
                                             message=f'Your book "{record.book.title}" is overdue. A fine of ₹{remaining} is due.',
                                             type='danger')
                            db.session.add(n)
                        elif unpaid_fine.amount != remaining:
                            unpaid_fine.amount = remaining
                    elif remaining <= 0 and unpaid_fine:
                        db.session.delete(unpaid_fine)
            db.session.commit()

    # Register blueprints
    from routes.landing  import landing_bp
    from routes.auth     import auth_bp
    from routes.admin    import admin_bp
    from routes.teacher  import teacher_bp
    from routes.student  import student_bp
    from routes.books    import books_bp
    from routes.api      import api_bp

    app.register_blueprint(landing_bp)
    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(admin_bp,   url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(books_bp,   url_prefix='/books')
    app.register_blueprint(api_bp,     url_prefix='/api')

    # Jinja2 globals
    from utils.helpers import format_date, time_ago
    app.jinja_env.globals.update(format_date=format_date, time_ago=time_ago)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
