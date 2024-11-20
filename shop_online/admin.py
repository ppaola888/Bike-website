from flask_login import current_user, login_required
from flask import Blueprint, render_template, redirect, url_for, flash, abort, current_app
from werkzeug.utils import secure_filename
from shop_online.forms import AddItemsForm, UpdateUserForm, DeleteForm
from shop_online.models import Product, User, ProductAttribute, ProductCategory, Order, OrderProduct
from shop_online import db
import os
import shutil
from datetime import datetime

admin = Blueprint('admin', __name__)


@admin.route('/users')
@login_required
def users_list():
    if current_user.is_admin:
        users = User.query.all()
        return render_template('users.html', users=users)
    return abort(403)


@admin.route('/update-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    if not current_user.is_admin:
        return abort(403)

    user = User.query.get_or_404(user_id)
    form = UpdateUserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        db.session.commit()
        flash('Utente aggiornato con successo!', 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('update_user.html', user=user, form=form)


@admin.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return abort(403)
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Utente eliminato con successo!', 'success')
    return redirect(url_for('admin.users_list'))


@admin.route('/display-items', methods=["GET", "POST"])
@login_required
def display_items():
    if not current_user.is_admin:
        return abort(403)

    products = Product.query.all()
    delete_form = DeleteForm()
    return render_template('display_items.html', products=products, form=delete_form)


def move_images(src_folder, dest_folder):
    """Spostare i file immagine dalla cartella di origine a quella di destinazione."""
    for filename in os.listdir(src_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            source_path = os.path.join(src_folder, filename)
            destination_path = os.path.join(dest_folder, filename)
            shutil.move(source_path, destination_path)


@admin.route('/add-items', methods=["GET", "POST"])
@login_required
def add_items():
    if not current_user.is_admin:
        return abort(403)

    form = AddItemsForm()
    if form.validate_on_submit():
        file = form.image.data
        file_name = None

        if file:
            file_name = secure_filename(file.filename)
            media_folder = os.path.join(current_app.static_folder, 'media')

            if not os.path.exists(media_folder):
                os.makedirs(media_folder)

            file_path = os.path.join(media_folder, file_name)
            file.save(file_path)

        category_enum = ProductCategory[form.category.data]

        new_product = Product(
            title=form.title.data,
            description=form.description.data,
            price=form.current_price.data,
            current_price=form.current_price.data,
            previous_price=form.previous_price.data,
            quantity=form.quantity.data,
            image=file_name if file else None,
            image_source='uploaded' if file else 'predefined',
            flash_sale=form.flash_sale.data,
            category=category_enum,
            date_added=datetime.utcnow()
        )

        if form.attributes.color.data or form.attributes.size.data:
            attribute = ProductAttribute(
                product=new_product,
                color=form.attributes.color.data,
                size=form.attributes.size.data,
                material=form.attributes.material.data,
                capacity=form.attributes.capacity.data
            )
            db.session.add(attribute)

        try:
            db.session.add(new_product)
            db.session.commit()

            move_images(media_folder, os.path.join(current_app.static_folder, 'images'))

            flash("Prodotto aggiunto con successo!", "success")
            return redirect(url_for('admin.display_items'))
        except Exception as e:
            db.session.rollback()
            flash(f"Errore durante l'aggiunta del prodotto: {e}", "danger")
            return render_template("error.html", error=str(e))
    return render_template("add_items.html", form=form)


@admin.route('/update-item/<int:product_id>', methods=["GET", "POST"])
@login_required
def update_item(product_id):
    if not current_user.is_admin:
        return abort(403)

    product = Product.query.get_or_404(product_id)
    form = AddItemsForm(obj=product)

    if form.validate_on_submit():
        file = form.image.data
        if file:
            file_name = secure_filename(file.filename)
            media_folder = os.path.join(current_app.static_folder, 'media')
            file_path = os.path.join(media_folder, file_name)

            if not os.path.exists(media_folder):
                os.makedirs(media_folder)

            file.save(file_path)
            product.image = file_name
            product.image_source = 'uploaded'

            move_images(media_folder, os.path.join(current_app.static_folder, 'images'))

        product.title = form.title.data
        product.description = form.description.data
        product.content = form.content.data
        product.current_price = form.current_price.data
        product.previous_price = form.previous_price.data
        product.flash_sale = form.flash_sale.data
        product.quantity = form.quantity.data
        product.category = form.category.data

        product_attribute = product.attributes[0] if product.attributes else ProductAttribute(product_id=product.id)
        product_attribute.size = form.attributes.size.data or product_attribute.size
        product_attribute.color = form.attributes.color.data or product_attribute.color
        product_attribute.material = form.attributes.material.data or product_attribute.material
        product_attribute.capacity = form.attributes.capacity.data or product_attribute.capacity

        try:
            if not product.attributes:
                db.session.add(product_attribute)
            db.session.commit()
            flash("Prodotto aggiornato con successo!", "success")
            return redirect(url_for('admin.display_items'))
        except Exception as e:
            db.session.rollback()
            flash(f"Errore durante l'aggiornamento del prodotto: {e}", "danger")

    return render_template('update_item.html', form=form, product=product)


@admin.route('/delete-item/<int:product_id>', methods=["POST"])
@login_required
def delete_item(product_id):
    if not current_user.is_admin:
        return abort(403)

    product = Product.query.get_or_404(product_id)

    ProductAttribute.query.filter_by(product_id=product_id).delete()

    try:
        db.session.delete(product)
        db.session.commit()
        flash("Prodotto eliminato con successo!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Errore durante l'eliminazione del prodotto.", "danger")

    return redirect(url_for('admin.display_items'))


@admin.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    if not current_user.is_admin:
        flash("Non hai i permessi per cancellare l'ordine.", "warning")
        return redirect(url_for('views.orders'))

    order = Order.query.get_or_404(order_id)

    try:
        order_products = OrderProduct.query.filter_by(order_id=order_id).all()
        for product in order_products:
            db.session.delete(product)

        db.session.delete(order)
        db.session.commit()
        flash(f"Ordine {order_id} eliminato con successo.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Errore nell'eliminazione dell'ordine: {str(e)}", "danger")
    return redirect(url_for('views.orders'))
