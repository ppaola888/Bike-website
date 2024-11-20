import random
from shop_online import create_app, db
from shop_online.models import User, Product, ProductAttribute, ProductCategory

app = create_app()


def clear_db():
    with app.app_context():
        db.session.query(ProductAttribute).delete()
        db.session.query(Product).delete()
        db.session.query(User).delete()
        db.session.commit()

        print("Database cancellato con successo!")


def populate_db():
    with app.app_context():
        db.create_all()

        # Users
        user = User(username='admin', email='admin@example.com', password='password123', is_admin=True)
        user1 = User(username='user1', email='user1@example.com', password='password124', is_admin=False)
        db.session.add(user)
        db.session.add(user1)
        db.session.commit()

        categories = [ProductCategory.biciclette, ProductCategory.bici_elettriche,
                      ProductCategory.monopattini, ProductCategory.accessori, ProductCategory.offerte]

        # Products attributes
        colors = ['Rosso', 'Blu', 'Verde', 'Nero', 'Grigio', 'Giallo', 'Bianco', 'Arancione']
        sizes = ['XS', 'S', 'M', 'L', 'XL']
        materials = ['Alluminio', 'Acciaio', 'Fibra di carbonio']

        for category in categories:
            for i in range(1, 13):
                # Solo ogni quarto prodotto nella categoria "offerte" è in offerta
                flash_sale = False
                if category == ProductCategory.offerte and i % 4 == 0:
                    flash_sale = True

                product = Product(
                    title=f"Prodotto {i} {category.name}",
                    description=f"Breve descrizione del prodotto {i} nella categoria {category.name}.",
                    content=f"Descrizione lunga e dettagliata del prodotto {i}. Questo prodotto è perfetto per chi cerca {category.name}. "
                            f"Offriamo alta qualità, materiali ricercati, componenti leggeri e resistenti. Stile, design modern, look pazzesco e soluzioni funzionali uniche!",
                    price=100.0 + (i * 10),
                    current_price=90.0 + (i * 8) if flash_sale else 100.0 + (i * 10),
                    previous_price=100.0 + (i * 10) if flash_sale else None,
                    flash_sale=flash_sale,
                    image=f"{category.name.lower()}{i}.jpg",
                    image_source='predefined',
                    rating=random.uniform(1, 5),
                    review_count=random.randint(0, 100),
                    quantity=random.randint(1, 50),
                    category=category
                )

                for color in colors:
                    for size in sizes:
                        for material in materials:
                            attribute = ProductAttribute(
                                product=product,
                                color=color,
                                size=size,
                                material=material,
                                capacity=random.choice([None, 100, 200, 300])
                            )
                            product.attributes.append(attribute)
                db.session.add(product)
                db.session.commit()


if __name__ == '__main__':
    clear_db()
    populate_db()
    print("Database popolato con successo!")
