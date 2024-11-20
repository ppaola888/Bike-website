from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from shop_online.models import User, Order, Product, ProductCategory, ProductAttribute, Wishlist, WishlistItem, Cart, \
    Review, OrderProduct, SearchQuery
from shop_online.forms import AddToCartForm, DeleteForm, ContactForm
from shop_online import db, os
import smtplib
import stripe

views = Blueprint('views', __name__)

PRODUCTS_PER_PAGE = 8


@views.route('/')
def index():
    new_arrivals = Product.query.order_by(Product.date_added.desc()).limit(4).all()
    return render_template('index.html', new_arrivals=new_arrivals)


@views.route('/new-arrivals')
def get_new_arrivals():
    new_arrivals = Product.query.order_by(Product.date_added.desc()).limit(4).all()
    return render_template('index.html', new_arrivals=new_arrivals)


@views.route('/profilo')
@login_required
def profilo():
    # print(f"Current User: {current_user}")
    is_admin = current_user.is_admin
    # print(f"User: {current_user.username}, Is Admin: {is_admin}")
    return render_template("admin.html", is_admin=is_admin)


@views.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 8
    search_type = request.args.get('type', '').strip()

    if not query:
        flash("Inserisci un termine di ricerca.", category="error")
        return redirect(url_for('views.index'))

    valid_search_types = ["id", "category", "title", "description", "color"]
    if search_type not in valid_search_types:
        flash("Tipo di ricerca non valido.", category="error")
        return redirect(url_for('views.index'))

    new_search_query = SearchQuery(query=query, search_type=search_type)
    db.session.add(new_search_query)
    db.session.commit()

    results = []

    if search_type == "id":
        try:
            product_id = int(query)
            results = Product.query.filter(Product.id == product_id).paginate(page=page, per_page=per_page)
        except ValueError:
            flash("L'ID deve essere un numero.", category="error")
            return redirect(url_for('views.index'))

    elif search_type == "category":
        singular_category = ProductCategory.singular(query.lower())
        if singular_category:
            results = Product.query.filter(Product.category == singular_category).paginate(page=page, per_page=per_page)
        else:
            results = Product.query.filter(Product.category.ilike(f"%{query.lower()}%")).paginate(page=page,
                                                                                                  per_page=per_page)

    elif search_type == "color":
        results = Product.query.join(ProductAttribute).filter(
            ProductAttribute.color.ilike(f"%{query}%")
        ).paginate(page=page, per_page=per_page)

    else:
        results = Product.query.filter(Product.title.ilike(f"%{query}%") |
                                       Product.description.ilike(f"%{query}%")).paginate(page=page, per_page=per_page)

    if not results.items:
        flash("Nessun prodotto trovato per la tua ricerca.", category="error")
    return render_template('search_results.html', query=query, results=results, search_type=search_type)


@views.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').strip()

    if len(query) < 3:
        return jsonify({'titles': [], 'categories': []})

    suggestions = Product.query.filter(
        (Product.title.ilike(f"{query}%")) |
        (Product.category.ilike(f"{query}%"))).limit(10).all()

    category_singulars = [ProductCategory.singular(cat) for cat in ProductCategory]

    results = {
        'titles': [product.title for product in suggestions],
        'categories': [product.category for product in suggestions] + list(filter(None, category_singulars))
    }
    return jsonify(results)


@views.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_item(product_id):
    product = Product.query.get_or_404(product_id)
    if not product:
        flash('Il prodotto non esiste.', 'danger')
        return redirect(url_for('views.index'))

    attributes = ProductAttribute.query.filter_by(product_id=product_id).all()

    page = request.args.get('page', 1, type=int)
    reviews_pagination = Review.query.filter_by(product_id=product_id).join(User).paginate(page=page, per_page=3,
                                                                                           error_out=False)
    category = request.args.get('category')
    product_page = request.args.get('product_page', 1, type=int)
    products_per_page = 10
    products_pagination = Product.query.filter_by(category=category).paginate(page=product_page,
                                                                              per_page=products_per_page,
                                                                              error_out=False)

    if request.method == 'POST':
        if 'add_to_cart' in request.form:
            size = request.form.get('size')
            color = request.form.get('color')
            quantity = request.form.get('quantity', 1)
            flash(f"Aggiunto {product.title} con taglia {size} e colore {color} al carrello.", 'success')
            return redirect(url_for('views.product_item', product_id=product.id))

        elif 'add_review' in request.form:
            rating = request.form.get('rating')
            comment = request.form.get('comment')
            if not rating or not comment:
                flash('Devi inserire un voto e un commento per la recensione.', 'danger')
            else:
                new_review = Review(user_id=current_user.id, product_id=product.id, rating=rating, comment=comment)
                db.session.add(new_review)
                db.session.commit()
                flash("Recensione aggiunta con successo!", 'success')
                return redirect(url_for('views.product_item', product_id=product.id))
    return render_template("products.html", product=product, attributes=attributes,
                           reviews_pagination=reviews_pagination, products_pagination=products_pagination,
                           is_single_product=True)


@views.route('/product/<int:product_id>/recensioni', methods=['GET', 'POST'])
def product_reviews(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        if not rating or not comment:
            flash("Devi inserire un voto e un commento per la recensione.", "error")
        else:
            new_review = Review(
                product_id=product.id,
                user_id=current_user.id,
                rating=int(rating),
                comment=comment
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Recensione aggiunta con successo!', 'success')
            return redirect(url_for('views.product_reviews', product_id=product.id))

    page = request.args.get('page', 1, type=int)
    reviews_pagination = Review.query.filter_by(product_id=product_id).join(User).paginate(page=page, per_page=3,
                                                                                           error_out=False)

    return render_template('recensioni.html', product=product, reviews_pagination=reviews_pagination)


@views.route('/offerte')
def offerte():
    offerte = Product.query.filter(Product.category == ProductCategory.offerte, Product.flash_sale == True
                                   ).all()
    return render_template('offerte.html', products=offerte)


@views.route('/products/<category>', methods=["GET"])
def view_products(category):
    page = request.args.get('page', 1, type=int)
    products = Product.query.filter_by(category=category).paginate(page=page, per_page=PRODUCTS_PER_PAGE,
                                                                   error_out=False)
    return render_template('products.html', products=products.items, pagination=products, category=category,
                           is_single_product=False)


@views.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        print("Il carrello è vuoto")
    else:
        print("Elementi nel carrello:", cart_items)

    total_price = sum([item.quantity * item.product.price for item in cart_items if item.product])

    cart_details = [
        {
            'id': item.id,
            'product': item.product,
            'quantity': item.quantity,
            'product_attribute': item.product_attribute,
            'color': item.product_attribute.color,
            'size': item.product_attribute.size,
            'price': item.product.price,
            'total': item.quantity * item.product.price
        }
        for item in cart_items if item.product_attribute
    ]
    empty_message = "Il tuo carrello è vuoto." if not cart_items else ""
    return render_template('cart.html', cart_details=cart_details, total_price=total_price, empty_message=empty_message)


@views.route('/add-to-cart/<int:product_id>/<int:attribute_id>', methods=["GET", "POST"])
@login_required
def add_to_cart(product_id, attribute_id):
    product = Product.query.get_or_404(product_id)
    product_attribute = ProductAttribute.query.get_or_404(attribute_id)
    form = AddToCartForm()

    quantity = int(request.form.get('quantity', 1))
    color = request.form.get('color') or product_attribute.color
    size = request.form.get('size') or product_attribute.size

    if not color or not size:
        flash('Colore o taglia non selezionati.', 'warning')
        return redirect(url_for('views.product_item', product_id=product_id))

    if quantity <= 0 or quantity > product.quantity:
        flash('Quantità non valida', 'warning')
        return redirect(url_for('views.product', product_id=product_id))

    cart_item = Cart.query.filter_by(
        product_id=product_id, user_id=current_user.id, product_attribute_id=attribute_id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        new_cart_item = Cart(product_id=product_id, user_id=current_user.id, quantity=quantity,
                             product_attribute_id=attribute_id)
        db.session.add(new_cart_item)

    db.session.commit()
    flash('Prodotto aggiunto al carrello.', 'success')
    print("Aggiunto al carrello, ID prodotto:", product_id, "ID attributo:", attribute_id)
    return redirect(url_for('views.cart'))


@views.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    action = request.form.get('action')
    cart_item = Cart.query.get_or_404(item_id)

    if cart_item.user_id != current_user.id:
        flash('Non hai il permesso di modificare questo elemento del carrello.', 'warning')
        return redirect(url_for('views.cart'))

    if action == 'increase':
        if cart_item.quantity < cart_item.product.quantity:
            cart_item.quantity += 1
            flash('Quantità del prodotto aggiunta.', 'success')
        else:
            flash(f'Quantità massima disponibile per {cart_item.product.title} raggiunta.', 'warning')
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            flash('Quantità del prodotto diminuita.', 'success')
        else:
            flash('La quantità non può essere inferiore a 1.', 'warning')

    db.session.commit()
    flash('Carrello aggiornato.', 'success')
    return redirect(url_for('views.cart'))


@views.route('/remove-from-cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = Cart.query.get_or_404(item_id)

    if cart_item and cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Prodotto rimosso dal carrello.', 'success')
    else:
        flash('Prodotto non trovato nel carrello.', 'warning')

    return redirect(url_for('views.cart'))


@views.route('/wishlist', methods=['GET', 'POST'])
@login_required
def wishlist():
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
    if wishlist:
        page = request.args.get('page', 1, type=int)
        wishlist_items = WishlistItem.query.filter_by(wishlist_id=wishlist.id).paginate(page=page, per_page=4)
    else:
        wishlist_items = []

    return render_template('wishlist.html', wishlist_items=wishlist_items)


@views.route('/wishlist_add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id):
    print(f"Received product_id: {product_id}")
    product = Product.query.get_or_404(product_id)
    if not product:
        flash("Errore: il prodotto specificato non esiste.", "error")
        return redirect(url_for('views.index'))

    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=current_user.id, product_id=0)
        db.session.add(wishlist)
        db.session.commit()

    existing_item = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
    if existing_item:
        flash("Prodotto già presente nella tua wishlist.", "info")
    else:
        new_item = WishlistItem(wishlist_id=wishlist.id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        flash("Prodotto aggiunto alla wishlist.", "success")

    return redirect(url_for('views.product_item', product_id=product_id))


@views.route('/wishlist_remove/<int:product_id>', methods=['POST'])
@login_required
def wishlist_remove(product_id):
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()

    if wishlist:
        wishlist_item_to_remove = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
        if wishlist_item_to_remove:
            db.session.delete(wishlist_item_to_remove)
            db.session.commit()
            flash('Prodotto rimosso dalla wishlist!', 'success')
        else:
            flash('Prodotto non trovato nella wishlist.', 'error')
    else:
        flash('Wishlist non trovata.', 'error')

    return redirect(url_for('views.wishlist'))


@views.route('/checkout')
@login_required
def checkout():
    stripe_public_key = current_app.config['STRIPE_PUBLIC_KEY']
    return render_template('checkout.html', stripe_public_key=stripe_public_key)


@views.route('/create-checkout-session', methods=["POST"])
def create_checkout_session():
    try:
        data = request.get_json()
        shipping_address = data.get('shipping_address')
        billing_address = data.get('billing_address')

        if not shipping_address or not billing_address:
            return jsonify(error="Shipping and billing addresses are required."), 400

        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            print("Cart is empty")
            return jsonify(error="Cart is empty"), 400

        line_items = []
        for item in cart_items:
            product = item.product
            line_items.append({
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': product.title,
                        'images': [product.image],
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': item.quantity,
            })

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode='payment',
            success_url=url_for('views.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('views.cancel', _external=True),
        )

        # Order object
        order = Order(
            user_id=current_user.id,
            total_price=session.amount_total / 100,
            payment_status='Pending',
            payment_id=session.id,
            quantity=sum(item.quantity for item in cart_items),
            shipping_address=shipping_address,
            billing_address=billing_address
        )

        # Add order to the database
        db.session.add(order)
        db.session.commit()

        for item in cart_items:
            order_product = OrderProduct(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_product)
        db.session.commit()

        return jsonify({'id': session.id})

    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return jsonify(error=e.user_message), 403
    except Exception as e:
        print(f"Error creating Stripe session: {e}")
        return jsonify(error=str(e)), 403


@views.route('/success', methods=["GET"])
def success():
    session_id = request.args.get('session_id')
    if not session_id:
        return "Errore: Sessione non trovata.", 400

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if not session:
            return "Errore: Impossibile recuperare i dettagli della sessione.", 400

        # payment = Payment.query.filter_by(session_id=session_id).first()

        if session.payment_status == "paid":
            order = Order.query.filter_by(payment_id=session_id).first()
            if order:
                order.payment_status = "paid"
                db.session.commit()

                Cart.query.filter_by(user_id=current_user.id).delete()
                db.session.commit()

                flash('Pagamento completato con successo!', 'success')
                return redirect(url_for('views.index'))
            else:
                return "Errore: Ordine non trovato.", 400

        flash('Pagamento non riuscito. Riprova.', 'error')
        return "Pagamento non riuscito.", 400

    except Exception as e:
        print(f"Error retrieving session: {e}")
        return "Errore durante il recupero della sessione.", 400


@views.route('/cancel')
def cancel():
    return redirect(url_for('views.cart'))


@views.route('/orders')
@login_required
def orders():
    delete_form = DeleteForm()
    page = request.args.get('page', 1, type=int)
    per_page = 9
    if current_user.is_admin:
        orders = Order.query.paginate(page=page, per_page=per_page)
        return render_template('orders.html', delete_form=delete_form, orders=orders, is_admin=True)
    user_orders = Order.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=per_page)
    return render_template('orders.html', delete_form=delete_form, orders=user_orders, is_admin=False)


@views.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def order_details(order_id):
    delete_form = DeleteForm()
    if current_user.is_admin:
        order = Order.query.get_or_404(order_id)
        return render_template('order_details.html', delete_form=delete_form, order=order,
                               is_admin=current_user.is_admin)
    else:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        return render_template('order_details.html', delete_form=delete_form, order=order, is_admin=False)


@views.route('/about')
def about():
    return render_template('about.html')


@views.route('/contatti', methods=["GET", "POST"])
def contatti():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form['subject']
            message = request.form.get('message')

            email_body = f"Nome: {name}\nEmail: {email}\nOggetto: {subject}\nMessaggio: {message}"

            try:
                MAIL_USERNAME = os.getenv('MAIL_USERNAME')
                MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(MAIL_USERNAME, MAIL_PASSWORD)
                    server.sendmail(
                        MAIL_USERNAME,
                        MAIL_USERNAME,
                    f"Subject: Nuovo messaggio dal modulo di contatto\n\n{email_body}"
                    )

                flash('Messaggio inviato con successo!', 'success')
                return redirect(url_for('views.index'))
            except Exception as e:
                flash(f"Errore nell'invio dell'email: {str(e)}", 'danger')
                return redirect(url_for('views.contatti'))

        else:
            flash('Errore nella validazione del modulo.', 'danger')
            print(form.errors)
    return render_template('contatti.html', form=form)


@views.route('/terms')
def terms():
    return render_template('terms.html')


@views.route('/privacy')
def privacy():
    return render_template('privacy.html')


@views.route('/faq')
def faq():
    return render_template('faq.html')


@views.route('/aiuto')
def aiuto():
    return render_template('aiuto.html')


@views.route('/reso')
def reso_ordine():
    return render_template('reso.html')


@views.route('/credits')
def credits():
    return render_template('credits.html')


@views.route('/subscribe_newsletter', methods=['POST'])
def subscribe_newsletter():
    # Implement the subscription logic here
    return redirect(url_for('views.index'))
