
# Bike Shop website

This project is an e-commerce web application that allows users to explore, purchase bicycles and accessories, and administrators to manage products, users, and orders. The app uses Flask as a backend framework and includes features for authentication, wishlist management, and integration with Stripe for payment. This e-commerce web application provides a complete shopping experience with both customer and admin functionalities.

## Features
**User Authentication**: Users and admin can register and access their profile securely (Passwords are hashed). They can also reset their password if they've forgotten it. Feedback messages (Flask messages) are displayed to inform users about login errors, password changes, or successful logins.

**Product View**: Users can explore bikes, accessories and special offers.

**Media Management**: Uploaded images are stored in static/media. After upload, they are automatically moved to static/images for use.

**Wishlist**: Users can add products to their wishlist.

**Shopping Cart**: Users can add products to their shopping cart and proceed to checkout.

**Checkout**: Integration with Stripe for secure payments. 

**Admin Access**: Only accounts with is_admin=True can access the admin routes.

**Product management**: Admin can add, update and delete products.

**Order management**: Admin can view and delete orders.

**User management**: Admin can delete users from the system.


## Technologies

- Python 3.7+
- Flask - Framework 
- SQLAlchemy - ORM 
- Flask-Login and hash password
- Flask-Migrate
- Stripe 
- Bootstrap - CSS 
- Jinja2 
- smtplib
- Stripe API keys (create a Stripe account at https://stripe.com/ to get test keys)

## Javascript Functionality 
- This project utilizes JavaScript to enhance user interaction and functionality.
- **Search Input Autocomplete**: An event listener is attached to the search input field to implement an autocomplete feature. This feature triggers when the user types at least three characters, fetching suggestions from the server based on the query.
- **Search Form Validation**: The script includes a function to validate the search form before submission. It checks that the query input is not empty and that a search type is selected. Error messages are displayed if validation fails.
- **Scroll to Top Button**: A button that allows users to scroll back to the top of the page smoothly when clicked. The button is only displayed after the user scrolls down a specified distance (300 pixels).

## Installation

**Clone the repository**: 

- git clone <repository-url>

- cd <repository-folder>

**Create a Virtual Environment**:

- python3 -m venv venv
- (Linux/macOS) source venv/bin/activate  
- (Windows) .\venv\Scripts\activate  

**Install Dependencies**:
- pip install -r requirements.txt

**Database Configuration**: 
- Ensure you have a database (SQLite or PostgreSQL) set up.
- Example: SQLALCHEMY_DATABASE_URI = 'sqlite:///bike_shop.db'
- Change the settings in the __init__.py file to connect to your database.

**Environment Variables**: Create a .env file and set the following variables:
- FLASK_APP='shop_online'
- FLASK_ENV='development' or 'production'
- SECRET_KEY=<your_secret_key>
- STRIPE_SECRET_KEY=<your_stripe_secret_key>
- STRIPE_PUBLIC_KEY=<your_stripe_public_key>

**Initialize the Database**:
- flask db init
- flask db migrate
- flask db upgrade

**Run the App**:
- flask run
- python main.py

**Open your browser and navigate to http://127.0.0.1:5000**

## File Organization

**__init__.py**: Sets up the Flask application instance. This file is essential for package-level initialization.

**main.py**: Main entry point for running the application. 

**auth.py**: Manages authentication, including login, logout and registration routes.

**admin.py**: Contains admin-related routes and functions, such as managing products and users.

**views.py**: Contains route definitions and view logic for general (non-admin) user interactions. It contains features that allow users to explore products, search for items, manage their shopping cart and wishlist, place orders, and interact with various information sections of the site.

**models.py**: Defines the data models used throughout the app, utilizing SQLAlchemy for ORM.

**forms.py**: Contains form classes for user input, like product creation, updating user profiles, etc.

**populate_db.py**: Script to seed the database with initial data, like default users, products, and categories.

**Directories**
- **static/**: All static files like CSS, JavaScript, and images 
- **templates/**: HTML templates for rendering dynamic content.
 The **base.html** template serves as a starting point for all pages. The **checkout.html** template collects shipping and billing information and initiates Stripe checkout.
The **profile.html** template displays user-specific content for both admin and customers.

## Routes

**Main Routes**:
- **/**: Main page showing new arrivals.
- **/new-arrivals**: Section dedicated to new arrivals.
- **/search**: Allows users to search for products with options such as title, category, color, etc.
- **/products/<category>**: Displays products filtered by category.
- **/product/<int:product_id>**: Shows the detail page of an individual product, allowing it to be added to the cart or to leave reviews.
- **/cart**: Cart management with options to view, update and remove items.
- **/checkout**: Section for payment and creating the payment session with Stripe.

**Wishlist Management**:

**Routes: /wishlist, /wishlist_add/<int:product_id>, /wishlist_remove/<int:product_id>**. Users can add/remove products in the wishlist and view saved items.

**Reviews and Ratings**:

**Route /product/<int:product_id>/reviews** to view and add reviews.

**Shopping Cart Management**:
- Functions to view cart contents (/cart), add items (/add-to-cart), and update or remove products from cart (/update_cart, /remove-from-cart).

**Checkout and Payment**:

- **Manage payment with Stripe**: (/create-checkout-session), payment confirmation (/success) and cancellation route (/cancel).

**Informational and Support Routes**:
Static sections such as /about, /contacts, /terms, /privacy, /faq, /help, and /reso, dedicated to general information and support.

## Database Structure
The application uses a relational database schema with **SQLAlchemy**(ORM) with the following table structure:

**Users** (User model): Stores user account information, including login credentials, role (is_admin for admins), and relationships to orders, cart items, wishlists, and reviews.

**Products** (Product model): Stores information about each product, including category, price, availability and other details.
Relationships with ProductAttribute (additional properties such as color and size), Review, Cart, WishlistItem and OrderProduct.

**Wishlist and WishlistItem** (models): Tracks products saved by users as potential future purchases. Each Wishlist is unique to a user and may contain multiple WishlistItem entries.

**Reviews** (Review model): Stores user-submitted ratings and comments for each product. Each Review is tied to both a user and a product, allowing customers to provide feedback on their purchases.

**Orders and Order Details** (Order and OrderProduct models): Represents orders placed by users and the specific products within each order. One-to-many relationship in Order, linking each order to the products it contains. Each order is associated with a specific user.

**Cart** (Cart model): Represents items currently added to the user’s cart but not yet ordered. Each cart item is associated with a user and with a product. Optional relationship to ProductAttribute(color, size, material).

**Payments** (Payment model): Stores payment details and status information for each order. Each Payment is linked to a user and an order, tracking the payment status for that transaction.

**Search Queries** (SearchQuery model): Tracks search terms entered by users.

# Usage

**Clear and Populate the Database**: 
- Run the populate_db.py script to seed your database with initial users, products, and categories
**Stripe’s test mode**:

- Log in to your Stripe account.
- Use the Stripe test card number 4242 4242 4242 4242 with any future expiration date and any three-digit CVC.

**Customer View**:
- Products: Search and view products available for purchase.
- Manage Cart: Add items to cart and view cart details.
- Checkout: Enter shipping and billing details, proceed with Stripe payment.
- Profile: View order history, wishlist, and change password.

**Admin View**:
- Manage Products: Add, modify, or remove products from the inventory.
- Manage Users: View and update user information.
- View Orders: Access all orders placed by customers.
- Change Password: Update admin password for security.

**Contact Form**:
- The contact form allows users to send messages directly to the site administrators. It is implemented in the /contatti route, and it utilizes Flask-WTF for form handling.

## Newsletter Subscription
- The functionality for subscribing to a newsletter has not been implemented. Future updates may include this feature.



























## 🛠 Skills
Flask, Flask-Login, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF, Bootstrap for styling, dotenv (for environment variable management), Javascript functionality



## 🚀 About Me
I'm a Python developer!

