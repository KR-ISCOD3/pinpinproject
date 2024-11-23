from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb
import os
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = 'your_unique_secret_key_here'  # Change this to a unique and secret value

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Set your MySQL password here
app.config['MYSQL_DB'] = 'test_db'  # Replace with your database name
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file extensions
def allowed_file(filename):
    # Allow all files by removing the check for allowed extensions
    return '.' in filename


# Route to render registration form
@app.route('/register')
def show_register_form():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))  # Redirect if already logged in
    return render_template('register.html')  # Render the HTML registration form


# Registration route
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    if not username or not email or not password:
        flash("All fields are required.")
        return redirect(url_for('register'))  # Or render the register page again

    # Check if the username or email already exists
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
    existing_user = cursor.fetchone()
    
    if existing_user:
        flash("Username or Email already exists.")
        return redirect(url_for('register'))
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        # Insert the new user
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, hashed_password))
        mysql.connection.commit()

        # Retrieve the user from the database
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        user = cursor.fetchone()

        # Set user session
        session['user_id'] = user['id']
        session['username'] = user['username']

        return redirect(url_for('show_login_form'))
    
    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f"Failed to register: {e}")
        return redirect(url_for('register'))  # Or render the register page again
    finally:
        cursor.close()


# Route to render login form
@app.route('/')
def show_login_form():
    error = request.args.get('error')
    error_message = "Invalid login credentials." if error == 'True' else None

    # if 'user_id' in session:
    #     return redirect(url_for('dashboard'))  # Redirect if already logged in

    return render_template('login.html', error_message=error_message)


# Login route
@app.route('/login', methods=['POST'])
def login():
    username_or_email = request.form['usernameoremail']
    password = request.form['password']
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (username_or_email, username_or_email)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('show_login_form', error=True))
    except MySQLdb.Error as e:
        return f"Error during login: {e}"
    finally:
        cursor.close()


# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Fetch count of customers, products, and orders
        cursor.execute("SELECT COUNT(*) AS customer_count FROM customer WHERE user_id = %s", (session['user_id'],))
        customer_count = cursor.fetchone()['customer_count']

        cursor.execute("SELECT COUNT(*) AS product_count FROM product WHERE user_id = %s", (session['user_id'],))
        product_count = cursor.fetchone()['product_count']

        cursor.execute("SELECT COUNT(*) AS order_count FROM `order` WHERE user_id = %s", (session['user_id'],))
        order_count = cursor.fetchone()['order_count']

        # Fetch total order amount
        cursor.execute("SELECT SUM(total) AS total_order_amount FROM `order` WHERE user_id = %s", (session['user_id'],))
        total_order_amount = cursor.fetchone()['total_order_amount'] or 0  # Default to 0 if no orders

        return render_template("dashboard.html", name=session['username'],
                               customer_count=customer_count, 
                               product_count=product_count,
                               order_count=order_count,
                               total_order_amount=total_order_amount)

    except MySQLdb.Error as e:
        flash(f"Error fetching dashboard data: {e}")
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()


# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('show_login_form'))


# Route to render the add product form
# @app.route('/add_product', methods=['GET'])
# def show_add_product_form():
#     if 'user_id' not in session:
#         return redirect(url_for('show_login_form'))
    
#     success = request.args.get('success', False)
#     return render_template('products.html', success=success)


# Route to handle product submission
@app.route('/add_product', methods=['POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in

    name = request.form['name']
    code = request.form['code']
    price = float(request.form['price'])
    stock = request.form['stock']
    description = request.form['description']
    file = request.files['image']

    # Check if the product code is unique
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # cursor.execute("SELECT * FROM product WHERE code = %s", (code,))
    # existing_product = cursor.fetchone()
    # if existing_product:
    #     flash("Product code already exists. Please use a different code.")
    #     return redirect(url_for('products'))

    # Validate the file type
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f"{app.config['UPLOAD_FOLDER']}/{filename}"
    else:
        flash("Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.")
        return redirect(url_for('products'))

    # Insert the product into the database
    try:
        cursor.execute(
            "INSERT INTO product (user_id, code, name, price, des, stock, image) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (session['user_id'], code, name, price, description, stock, image_path)
        )
        mysql.connection.commit()

        return redirect(url_for('products'))  # Redirect to products page after successful insert
    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f"Failed to add product: {e}")
        return redirect(url_for('products'))
    finally:
        cursor.close()


# Route to fetch and display all products
@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM product WHERE user_id = %s", (session['user_id'],))
        products = cursor.fetchall()
        return render_template('products.html', products=products, name=session['username'])
    except MySQLdb.Error as e:
        flash(f"Failed to fetch products: {e}")
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()


@app.route('/edit_product', methods=['POST'])
def update_product():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in

    product_id = request.form.get('product_id')
    name = request.form.get('upname')
    code = request.form.get('upcode')
    price = float(request.form.get('upprice', 0))
    stock = request.form.get('upstock')
    description = request.form.get('updescription')
    file = request.files.get('upimage')

    # Fetch current product details to retain current image if no new one is uploaded
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT image FROM product WHERE id = %s AND user_id = %s", 
                   (product_id, session['user_id']))
    product = cursor.fetchone()
    current_image = product['image'] if product else None

    image_path = current_image  # Default to current image path

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f"{app.config['UPLOAD_FOLDER']}/{filename}"

    try:
        if product_id:  # Ensure product_id is valid
            cursor.execute(""" 
                UPDATE product 
                SET name = %s, code = %s, price = %s, des = %s, stock = %s, image = %s 
                WHERE id = %s AND user_id = %s
            """, (name, code, price, description, stock, image_path, product_id, session['user_id']))
            mysql.connection.commit()
            flash("Product updated successfully!")
        else:
            flash("Invalid product ID.")
        
        return redirect(url_for('products'))

    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f"Failed to update product: {e}")
        return redirect(url_for('products'))
    finally:
        cursor.close()


# Route to handle product deletion
@app.route('/delete_product', methods=['POST'])
def delete_product():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in

    id = request.form['del_id']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # First, fetch the product details to check if the image exists
        cursor.execute("SELECT image FROM product WHERE id = %s AND user_id = %s", (id, session['user_id']))
        product = cursor.fetchone()

        if not product:
            flash("Product not found.")
            return redirect(url_for('products'))  # Redirect to products if not found

        # Delete product from the database
        cursor.execute("DELETE FROM product WHERE id = %s AND user_id = %s", (id, session['user_id']))
        mysql.connection.commit()

        # If the image exists, delete it from the server
        if product['image'] and os.path.exists(product['image']):
            os.remove(product['image'])

        flash("Product deleted successfully!")
        return redirect(url_for('products'))

    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f"Failed to delete product: {e}")
        return redirect(url_for('products'))
    finally:
        cursor.close()

# Route to handle order processing
@app.route('/process_order', methods=['POST'])
def order_process():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Ensure the user is logged in

    # Retrieve the order details from the form (JSON string containing list of orders)
    order_details = request.form.get('order_details')  # This will be a JSON string

    try:
        order_details = json.loads(order_details)
    except ValueError as e:
        flash("Invalid order data received.")
        return redirect(url_for('products'))  # Redirect to products if invalid order data

    # Retrieve customer information from the form
    customer_name = request.form.get('name')
    customer_tel = request.form.get('tel')
    customer_location = request.form.get('location')

    # Start a database transaction
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Step 1: Insert new customer data (no need to check if customer already exists)
        cursor.execute("""
            INSERT INTO customer (name, tel, location, date, user_id) 
            VALUES (%s, %s, %s, NOW(), %s)
        """, (customer_name, customer_tel, customer_location, session['user_id']))

        # Step 2: Get the customer_id of the newly inserted customer
        cursor.execute("SELECT LAST_INSERT_ID()")
        customer_id = cursor.fetchone()['LAST_INSERT_ID()']

        # Step 3: Insert each ordered item into the order table
        for order in order_details:
            cursor.execute("""
                INSERT INTO `order` (product_id, customer_id, user_id, qty, total, date) 
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (order['product_id'], customer_id, session['user_id'], order['qty'], order['total']))

        # Commit the transaction
        mysql.connection.commit()

        flash("Order processed successfully!")
        return redirect(url_for('products'))

    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f"Error processing order: {e}")
        return redirect(url_for('products'))
    finally:
        cursor.close()

@app.route('/order')
def fetch_orders():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Ensure the user is logged in

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Execute the SQL query
        cursor.execute("""
            SELECT 
                o.id AS order_id,
                p.name AS product_name,
                o.qty,
                p.price,
                o.total,
                c.name AS customer_name,
                c.tel AS customer_tel,
                c.location AS customer_location,
                DATE(o.date) AS order_date
            FROM `order` o
            JOIN `product` p ON o.product_id = p.id
            JOIN `customer` c ON o.customer_id = c.id
            WHERE o.user_id = %s
            ORDER BY o.date DESC;
        """, (session['user_id'],))
        
        # Fetch the data
        orders = cursor.fetchall()
        return render_template('orderRecord.html', orders=orders,name=session['username'])

    except MySQLdb.Error as e:
        return render_template('error.html', message=f"Error: {e}")

    finally:
        cursor.close()

@app.route('/customer')
def fetch_customers():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Ensure the user is logged in

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Execute the SQL query to fetch customer data
        cursor.execute("""
            SELECT 
                id AS customer_id,
                name AS customer_name,
                tel AS customer_tel,
                location AS customer_location,
                DATE(date) AS customer_date
            FROM customer
            WHERE user_id = %s
            ORDER BY date DESC;
        """, (session['user_id'],))
        
        # Fetch the data
        customers = cursor.fetchall()
        return render_template('customerRecord.html', customers=customers, name=session['username'])

    except MySQLdb.Error as e:
        return render_template('error.html', message=f"Error: {e}")

    finally:
        cursor.close()

@app.route('/search_products', methods=['GET'])
def search_products():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in

    query = request.args.get('query', '').strip()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Search for products matching the query in the name, code, or description
        cursor.execute("""
            SELECT * FROM product 
            WHERE user_id = %s 
            AND (name LIKE %s OR code LIKE %s OR des LIKE %s)
        """, (session['user_id'], f"%{query}%", f"%{query}%", f"%{query}%"))
        products = cursor.fetchall()

        return render_template('products.html', products=products, name=session['username'])
    except MySQLdb.Error as e:
        flash(f"Failed to search products: {e}")
        return redirect(url_for('products'))
    finally:
        cursor.close()

if __name__ == '__main__':
    app.run(debug=True)
