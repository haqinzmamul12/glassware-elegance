from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os 
import uvicorn  
import time
import uuid 
from datetime import datetime
from backend.retriever import hybrid_search
from src.email import send_email
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, CartItem, Orders
from flask_login import LoginManager, login_user
from flask_login import current_user, logout_user, login_required


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'



# db.init_app(app)

# #Setup LoginManager

# login_manager = LoginManager()
# login_manager.init_app(app)

# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))



db.init_app(app)

# Setup LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirects to /login if not authenticated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form['email']
        password = request.form['password']

        # Find by email or username
        user = User.query.filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()

        if not user:
            flash("User does not exist. Please sign up first.", "error")
            return redirect(url_for('login'))

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Try again.")
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Simple check for password match
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('signup'))

        # Check if email or username already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash("Email or username already exists.")
            return redirect(url_for('signup'))

        # Save new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please log in.")
        return redirect(url_for('login'))

    return render_template('signup.html')



@app.route('/account')
@login_required
def account():
    return render_template('account.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))





@app.route('/')
def home():
    return render_template('base.html')

@app.route('/about')
def about():
    return render_template('about.html', active_page='about')



# Route for contact page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Basic validation
        if not name or not email or not message:
            flash("All fields are required!", "danger")
            return redirect(url_for('contact'))

        try:
            # Send the email
            send_email(name, email, message)
            flash("Message sent successfully!", "success")
        except Exception as e:
            print(f"Error sending message: {e}")
            flash("An error occurred while sending your message.", "danger")

        return redirect(url_for('contact'))

    return render_template('contact.html', active_page='contact')






@app.route('/add_address', methods=['POST'])
@login_required
def add_address():
    full_name = request.form.get('full_name')
    address = request.form.get('address')
    city = request.form.get('city')
    pincode = request.form.get('pincode')
    phone = request.form.get('phone')

    full_address = f"{full_name}, {address}, {city} - {pincode}, Phone: {phone}"
    current_user.address = full_address
    db.session.commit()

    flash("Address added successfully!", "success")
    return redirect(url_for('checkout'))


@app.route('/change_address', methods=['GET', 'POST'])
@login_required
def change_address():
    if request.method == 'POST':
        new_address = request.form.get('address')
        current_user.address = new_address
        db.session.commit()
        flash("Address updated successfully!", "success")
        return redirect(url_for('checkout'))

    return render_template('change_address.html', current_address=current_user.address)




# @app.route('/confirm_payment', methods=['POST'])
# @login_required
# def confirm_payment():
#     payment_method = request.form.get('payment_method')
#     # Here you’d typically trigger payment gateway or confirm order
#     flash(f"Order placed successfully using {payment_method.capitalize()}!")
#     session.pop('cart', None)
#     return redirect(url_for('home'))


# ----------------------------
# Lesson 4 — Confirm payment and clear user cart
# ----------------------------
@app.route('/confirm_payment', methods=['POST'])
@login_required
def confirm_payment():
    payment_method = request.form.get('payment_method', 'unknown')
    try: 
        cart_items = CartItem.query.filter_by(
            username=current_user.username,
            saved_for_later=False
        ).all()

        if not cart_items:
            flash("Your cart is empty!", "warning")
            return redirect(url_for('checkout'))
        
        for item in cart_items:
            orders = Orders(
                id=str(uuid.uuid4())[:12],  # generate unique order ID
                date=datetime.now().strftime("%d %B %Y"),
                total=f"₹{item.product.price}",
                ship_to=current_user.username,
                status="Order Placed",
                status_msg="Your order is in progress",
                item_name=item.product.name,
                item_img=item.product.image_url,
                user_id=current_user.id
            )
            db.session.add(orders)

        # ✅ Now clear cart items
        deleted_count = db.session.query(CartItem) \
            .filter(
                CartItem.username == current_user.username,
                CartItem.saved_for_later == False
            ).delete(synchronize_session=False)

        db.session.commit()
        session['cart_count'] = get_cart_count()

    except Exception as e:
        db.session.rollback()
        print("Error in confirm_payment:", e)  # debugging
        flash("An error occurred while processing payment. Please try again.", "danger")
        return redirect(url_for('checkout'))

    # ✅ Render a page that waits & redirects
    return render_template("order_success.html", payment_method=payment_method)




@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    filtered_products =[] 

    if query:
        filtered_products = hybrid_search(query, k=3)
    
    if not filtered_products:
        flash("No relevant products found. Try a different search.", "warning")
        return redirect(url_for("products"))


    return render_template('products.html', products=filtered_products, query=query)



# Dummy product data — replace or load from DB later
with open('products.json', 'r') as f:
    products_data = json.load(f)



@app.route('/products')
def products():
    return render_template('products.html', products=products_data, active_page='products')



@app.route('/cart')
def cart():
    if current_user.is_authenticated:
        active_items = CartItem.query.filter_by(username=current_user.username, saved_for_later=False).all()
        saved_items = CartItem.query.filter_by(username=current_user.username, saved_for_later=True).all()

        # # 🔽 ADD THESE DEBUG PRINTS
        # print("ACTIVE ITEMS (saved_for_later=False):", [i.product.name for i in active_items])
        # print("SAVED ITEMS (saved_for_later=True):", [i.product.name for i in saved_items])
        # print("\n--- CART ROUTE DEBUG ---")
        # print(f"Active items: {[ (i.product.name, i.saved_for_later) for i in active_items ]}")
        # print(f"Saved items: {[ (i.product.name, i.saved_for_later) for i in saved_items ]}")
        # print("--- END DEBUG ---\n")


        cart = {}
        total = 0
        for item in active_items:
            cart[item.product.name] = {
                'id': item.product.id,
                'price': item.product.price,
                'description': item.product.description,
                'image_url': item.product.image_url,
                'quantity': item.quantity
            }
            total += item.product.price * item.quantity


        saved = {}
        for item in saved_items:
            saved[item.product.name] = {  
                'id': item.product.id,
                'price': item.product.price,
                'description': item.product.description,
                'image_url': item.product.image_url,
                'quantity': item.quantity
                }
            
    else:
        # Guest user → use session
        cart = session.get('cart', {})
        saved = session.get('saved', {})
        total = sum(item['price'] * item['quantity'] for item in cart.values())

    return render_template('cart.html', cart=cart, saved=saved, total=total, active_page='cart')






def get_cart_count():
    if current_user.is_authenticated:
        return db.session.query(db.func.sum(CartItem.quantity))\
            .filter_by(username=current_user.username).scalar() or 0
    else:
        return session.get('cart_count', 0)



@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    id = int(request.form.get('product_id'))  # ensure integer
    name = request.form.get('product_name')
    price = float(request.form.get('product_price'))
    description = request.form.get('product_description')
    image_url = request.form.get('product_image_url')

    if current_user.is_authenticated:
        # Logged-in user → save to DB
        product = Product.query.get(id)
        if not product:
            # If product not in DB, insert it
            product = Product(
                id=id,
                name=name,
                description=description,
                price=price,
                image_url=image_url
            )
            db.session.add(product)
            db.session.commit()

        cart_item = CartItem.query.filter_by(username=current_user.username, product_id=id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(username=current_user.username, product_id=id, quantity=1)
            db.session.add(cart_item)

        db.session.commit()
        session['cart_count'] = get_cart_count()
        flash(f"{name} added to your cart.")

    else:
        # Guest user → session cart
        cart = session.get('cart', {})
        if name in cart:
            cart[name]['quantity'] += 1
        else:
            cart[name] = {
                'id': id,
                'price': price,
                'description': description,
                'image_url': image_url,
                'quantity': 1
            }
        session['cart'] = cart
        session['cart_count'] = sum(item['quantity'] for item in cart.values())
        flash(f"{name} added to cart.")

    return redirect(url_for('products'))





@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_name = request.form.get('product_name')
    action = request.form.get('action')

    if current_user.is_authenticated:
        product = Product.query.filter_by(name=product_name).first()
        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for('cart'))

        item = CartItem.query.filter_by(
            username=current_user.username,
            product_id=product.id,
            saved_for_later=False
        ).first()

        if not item:
            flash("Item not in your cart.", "warning")
            return redirect(url_for('cart'))

        if action == 'increase':
            item.quantity += 1
        elif action == 'decrease':
            item.quantity -= 1
            if item.quantity <= 0:
                db.session.delete(item)
        elif action == 'remove':
            db.session.delete(item)

        db.session.commit()
        session['cart_count'] = get_cart_count()
        return redirect(url_for('cart'))

    # -------- Guest (session) logic --------
    cart = session.get('cart', {})
    if product_name in cart:
        if action == 'increase':
            cart[product_name]['quantity'] += 1
        elif action == 'decrease':
            cart[product_name]['quantity'] -= 1
            if cart[product_name]['quantity'] <= 0:
                del cart[product_name]
        elif action == 'remove':
            del cart[product_name]

    session['cart'] = cart
    session['cart_count'] = sum(item['quantity'] for item in cart.values())
    return redirect(url_for('cart'))



@app.route('/checkout', methods=['GET'])
@login_required
def checkout():
    return render_template('checkout.html', user=current_user)




@app.route('/cart_action', methods=['POST'])
def cart_action():
    product_name = request.form.get('product_name')
    action = request.form.get('action')

    if current_user.is_authenticated:
        product = Product.query.filter_by(name=product_name).first()
        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for('cart'))

        item = CartItem.query.filter_by(
            username=current_user.username,
            product_id=product.id
        ).first()

        if not item:
            flash("Item not found.", "warning")
            return redirect(url_for('cart'))

        if action == 'save':
            item.saved_for_later = True
            db.session.commit()
            flash("Item moved to Saved for Later.", "info")



        elif action == 'share':
            print(f"User wants to share: {product_name}")

        session['cart_count'] = get_cart_count()
        return redirect(url_for('cart'))
    
    else:
        # ---------- Guest logic (sessions) ----------
        cart = session.get('cart', {})
        saved = session.get('saved', {})

        if action == 'save':
            if product_name in cart:
                # move from cart -> saved
                saved[product_name] = cart[product_name]
                del cart[product_name]
                flash("Item moved to Saved for Later.", "info")

        elif action == 'share':
            print(f"[Guest] User wants to share: {product_name}")

    session['cart'] = cart
    session['saved'] = saved
    session['cart_count'] = sum(item['quantity'] for item in cart.values())

    return redirect(url_for('cart'))




@app.route('/move_to_cart', methods=['POST'])
def move_to_cart():
    #product_name = request.form.get('product_name')

    product_name = request.form.get('product_name')
    action = request.form.get('action')

    if not product_name or not action:
        flash("Invalid request.", "warning")
        return redirect(url_for('cart'))

    if current_user.is_authenticated:
        product = Product.query.filter_by(name=product_name).first()
        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for('cart'))

        # Fetch the item specifically from Saved-for-Later
        saved_item = CartItem.query.filter_by(
            username=current_user.username,
            product_id=product.id,
            saved_for_later=True
        ).first()

        if not saved_item:
            flash("Item not found in Saved for Later.", "warning")
            return redirect(url_for('cart'))

        if action == "moveback":
            # If an active (not-saved) item already exists for same product, merge quantities
            active_item = CartItem.query.filter_by(
                username=current_user.username,
                product_id=product.id,
                saved_for_later=False
            ).first()

            if active_item:
                active_item.quantity += saved_item.quantity
                db.session.delete(saved_item)
                #print(f"[DEBUG] Merging saved item {product.name} into active cart, new qty={active_item.quantity}")
                flash("Item moved to cart — quantities merged.", "success")
            else:
                # just flip the flag back to active cart
                saved_item.saved_for_later = False
                #print(f"[DEBUG] Moving {product.name} back to active cart, saved_for_later={saved_item.saved_for_later}")
                flash("Item moved to Cart.", "success")

            db.session.commit()

        elif action == "remove":
            # remove only the saved item
            print(f"[DEBUG] Removing {product.name} from Saved for Later (id={saved_item.id})")

            db.session.delete(saved_item)
            db.session.commit()
            #print(f"[DEBUG] DB committed remove for {product.name}")
            flash("Item removed from Saved for Later.", "danger")

        else:
            flash("Unknown action.", "warning")

        session['cart_count'] = get_cart_count()
        return redirect(url_for('cart'))


    # -------- Guest (session) logic unchanged --------
    saved = session.get('saved', {})
    cart = session.get('cart', {})

    if product_name in saved:
        cart[product_name] = saved[product_name]
        del saved[product_name]

    session['cart'] = cart
    session['saved'] = saved
    session['cart_count'] = sum(item['quantity'] for item in cart.values())
    return redirect(url_for('cart'))



@app.route('/orders')
def fetch_orders():
    # Example: fetch orders from DB in real app
    user_orders = Orders.query.filter_by(user_id=current_user.id).all()

    if not user_orders:
        flash("You have not placed any orders yet.", "info")

    return render_template("orders.html", orders=user_orders)


@app.route('/track-order')
@login_required
def track_orders():
    # Fetch all orders of the current logged-in user
    orders = Orders.query.filter_by(user_id=current_user.id).all()
    return render_template('track.html', orders=orders)



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render sets the PORT env var
    app.run(host='0.0.0.0', port=port)

