from shop_online import db
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from shop_online.forms import LoginForm, RegisterForm, PasswordChangeForm, ResetPasswordForm, ForgotPasswordForm
from shop_online.models import User
from flask_mail import Message
from shop_online import mail

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash('Ti sei già iscritto con questa email, effettua il login!', 'warning')
            return redirect(url_for('auth.login'))

        new_user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Registrazione effettuata con successo!', 'success')
        return redirect(url_for('views.index'))

    return render_template("register.html", form=form)


@auth.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        # Email doesn't exist
        if not user:
            flash('L\'email non esiste, riprovare.', 'error')
            return redirect(url_for('auth.login'))
        # Password incorrect
        elif not user.check_password(password):
            flash('La password non è corretta, riprovare.', 'error')
            return redirect(url_for('auth.login'))
        else:
            login_user(user)
            flash('Log in effettuato con successo!', 'success')
            return redirect(url_for("views.index"))
    return render_template("login.html", form=form)


@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('Se l\'indirizzo email è valido, riceverai un link per il reset della password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Richiesta di Reset Password',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'''Per resettare la tua password clicca sul link seguente:
{url_for('auth.reset_password_token', token=token, _external=True)}

Se non hai richiesto il reset della password, ignora questa email.
'''
    mail.send(msg)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('Il token è invalido o è scaduto.', 'warning')
        return redirect(url_for('auth.reset_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('La tua password è stata aggiornata con successo. Ora puoi effettuare l\'accesso.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password_token.html', form=form, token=token)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo!', 'success')
    return redirect(url_for('views.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('La password corrente è errata.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password cambiata con successo!', 'success')
            return redirect(url_for('views.profilo'))
    return render_template('change_password.html', form=form)
