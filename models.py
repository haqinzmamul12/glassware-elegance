from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text) 


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image_url = db.Column(db.String(200))

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), db.ForeignKey('user.username'))  # changed to username
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    saved_for_later = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='cart_items', foreign_keys=[username])
    product = db.relationship('Product')


class Orders(db.Model):
    id = db.Column(db.String(50), primary_key=True)   # unique order id
    date = db.Column(db.String(50), nullable=False)
    total = db.Column(db.String(20), nullable=False)
    ship_to = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Order Placed")
    status_msg = db.Column(db.String(200), default="Order Placed")
    item_name = db.Column(db.String(300), nullable=False)
    item_img = db.Column(db.String(300), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
