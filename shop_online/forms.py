from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, EmailField, PasswordField, SubmitField, \
    SelectField, FloatField, IntegerField, BooleanField, HiddenField, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange, URL
from shop_online.models import ProductCategory


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField("Login")


class ProductAttributeForm(FlaskForm):
    size = StringField('Taglia', validators=[Optional()])
    color = StringField('Colore', validators=[Optional()])
    material = StringField('Materiale', validators=[Optional()])
    capacity = IntegerField('Capacità', validators=[Optional()])


class AddItemsForm(FlaskForm):
    title = StringField('Titolo', validators=[DataRequired()])
    description = TextAreaField('Descrizione', validators=[DataRequired()])
    content = TextAreaField('Contenuto', validators=[Optional()])
    current_price = FloatField('Prezzo Corrente', validators=[DataRequired(), NumberRange(min=0)])
    previous_price = FloatField('Prezzo Precedente', validators=[Optional(), NumberRange(min=0)])
    flash_sale = BooleanField('In Offerta', default=False)
    image = FileField('Immagine del Prodotto', validators=[Optional()])
    image_source = StringField('Image Source', validators=[Optional(), URL()])
    category = SelectField('Categoria', choices=[(category.value, category.value) for category in ProductCategory],
                           validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=1)])
    quantity = IntegerField('Quantità', default=0)
    rating = IntegerField('Rating', validators=[Optional(), NumberRange(min=1, max=5)])
    review_count = IntegerField('Review Count', default=0)
    attributes = FormField(ProductAttributeForm)


class DeleteForm(FlaskForm):
    submit = SubmitField('Elimina')


class OrderForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=60)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=20)])
    address = TextAreaField("Address", validators=[DataRequired(), Length(min=10, max=200)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=50)])
    postal_code = StringField('Postal Code', validators=[DataRequired(), Length(min=5, max=10)])

    payment_method = SelectField('Payment Method', choices=[('stripe', 'Stripe'), ('paypal', 'PayPal')],
                                 validators=[DataRequired()])

    additional_notes = TextAreaField('Additional Notes', validators=[Length(max=500)])

    submit = SubmitField('Place Order')


class ProfileForm(FlaskForm):
    username = StringField('Nome Utente', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Aggiorna')


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Password Attuale', validators=[DataRequired(), Length(min=6)])
    new_password = PasswordField('Nuova Password', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Conferma Nuova Password',
                                         validators=[DataRequired(), EqualTo('new_password')])
    change_password = SubmitField('Cambia Password')


class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Richiedi Password Dimenticata')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nuova Password', validators=[DataRequired(), Length(min=8, message='La password deve avere almeno 8 caratteri.')])
    confirm_password = PasswordField('Conferma Nuova Password',
                                     validators=[DataRequired(), Length(min=8, message='La password deve avere almeno 8 caratteri.'),
                                                 EqualTo('password', message="Le password devono coincidere")])
    submit = SubmitField('Resetta Password')


class UpdateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Ruolo Admin')
    submit = SubmitField('Aggiorna Utente')


class AddToCartForm(FlaskForm):
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity',
                            validators=[DataRequired(), NumberRange(min=1, message='Quantity must be at least 1')])
    submit = SubmitField("Add To Cart")


class WishlistForm(FlaskForm):
    # product_id = IntegerField('Product ID', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add to Wishlist')


class ContactForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Oggetto', validators=[DataRequired()])
    message = TextAreaField('Messaggio', validators=[DataRequired()])
