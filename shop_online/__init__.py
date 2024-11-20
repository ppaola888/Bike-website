from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_mail import Mail
import os
from dotenv import load_dotenv
import stripe

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['MEDIA_FOLDER'] = os.getenv('MEDIA_FOLDER', 'static/media')
    print("Database URI:", os.getenv('DATABASE_URI'))
    app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
    app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
    app.config['WTF_CSRF_ENABLED'] = True

    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    # Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf = CSRFProtect(app)
    mail.init_app(app)

    @app.context_processor
    def inject_wishlist_count():
        wishlist_count = 0
        if current_user.is_authenticated:
            user_wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
            wishlist_count = len(user_wishlist.items) if user_wishlist else 0
        return dict(wishlist_count=wishlist_count)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    from shop_online.models import Wishlist
    from .views import views
    from .auth import auth
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')

    return app
