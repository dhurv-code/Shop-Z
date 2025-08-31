from flask import Flask, render_template, redirect, url_for, request, session, flash
import sqlite3
from products import products

app = Flask(__name__)
app.secret_key = "supersecretkey"


def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS carts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER
                )''')
    conn.commit()
    conn.close()

init_db()


def get_user_cart(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT product_id FROM carts WHERE user_id=?", (user_id,))
    cart_product_ids = [row[0] for row in c.fetchall()]
    conn.close()
    cart_items = [p for p in products if p['id'] in cart_product_ids]
    return cart_items

@app.context_processor
def utility_processor():
    return dict(get_user_cart=get_user_cart)


@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
        conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = username
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash("Login first to add to cart!", "warning")
        return redirect(url_for('login'))
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("INSERT INTO carts (user_id, product_id) VALUES (?, ?)", (session['user_id'], product_id))
    conn.commit()
    conn.close()
    flash("Product added to cart!", "success")
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'user_id' not in session:
        flash("Login first to modify cart!", "warning")
        return redirect(url_for('login'))
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("DELETE FROM carts WHERE user_id=? AND product_id=?", (session['user_id'], product_id))
    conn.commit()
    conn.close()
    flash("Item removed from cart.", "info")
    return redirect(url_for('cart'))

@app.route('/buy_now/<int:product_id>')
def buy_now(product_id):
    if 'user_id' not in session:
        flash("Login first to buy!", "warning")
        return redirect(url_for('login'))
    product = next((p for p in products if p['id'] == product_id), None)
    return render_template('checkout.html', total=product['price'], buy_now_product=product)

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash("Login first to view cart!", "warning")
        return redirect(url_for('login'))
    cart_items = get_user_cart(session['user_id'])
    total = sum(item['price'] for item in cart_items)
    return render_template('cart.html', cart=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash("Login first!", "warning")
        return redirect(url_for('login'))

    if request.method == 'GET':
        cart_items = get_user_cart(session['user_id'])
        total = sum(item['price'] for item in cart_items)
        return render_template('checkout.html', cart=cart_items, total=total)

    elif request.method == 'POST':
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute("DELETE FROM carts WHERE user_id=?", (session['user_id'],))
        conn.commit()
        conn.close()
        flash("Payment successful! Thank you for your purchase.", "success")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
