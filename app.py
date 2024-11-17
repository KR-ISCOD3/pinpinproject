from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb
import os
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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, hashed_password))
        mysql.connection.commit()

        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        user = cursor.fetchone()

        session['user_id'] = user['id']
        session['username'] = user['username']

        return redirect(url_for('dashboard'))
    
    except MySQLdb.Error as e:
        mysql.connection.rollback()
        return f"Failed to register: {e}"
    finally:
        cursor.close()


# Route to render login form
@app.route('/')
def show_login_form():
    error = request.args.get('error')
    error_message = "Invalid login credentials." if error == 'True' else None

    if 'user_id' in session:
        return redirect(url_for('dashboard'))  # Redirect if already logged in

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
    return render_template("dashboard.html", name=session['username'])


# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('show_login_form'))


# Route to render the add product form
@app.route('/add_product')
def show_add_product_form():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))
    
    success = request.args.get('success', False)
    return render_template('products.html', success=success)


# Route to handle product submission
@app.route('/add_product', methods=['POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))

    name = request.form['name']
    code = request.form['code']
    price = float(request.form['price'])
    stock = request.form['stock']
    description = request.form['description']
    file = request.files['image']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f"{app.config['UPLOAD_FOLDER']}/{filename}"
    else:
        flash("Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.")
        return redirect(url_for('add_product'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(
            "INSERT INTO product (user_id, code, name, price, des, stock, image) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (session['user_id'], code, name, price, description, stock, image_path)
        )
        mysql.connection.commit()

        flash("Product added successfully!")
        return redirect(url_for('products'))
    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f"Failed to add product: {e}")
        return redirect(url_for('add_product'))
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


# Route to handle product update
@app.route('/edit_product', methods=['POST'])
def update_product():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in

    id = request.form['product_id']
    name = request.form['upname']
    code = request.form['upcode']
    price = float(request.form['upprice'])
    stock = request.form['upstock']
    description = request.form['updescription']
    file = request.files['upimage']
    image_path = None

    # If a new file is uploaded, process it
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f"{app.config['UPLOAD_FOLDER']}/{filename}"
    
    # If no new file is uploaded, keep the current image
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if image_path:  # If a new image is uploaded, update the image path
            cursor.execute(""" 
                UPDATE product 
                SET name = %s, code = %s, price = %s, des = %s, stock = %s, image = %s 
                WHERE id = %s AND user_id = %s
            """, (name, code, price, description, stock, image_path, id, session['user_id']))
        else:  # If no image is uploaded, update without changing the image
            cursor.execute(""" 
                UPDATE product 
                SET name = %s, code = %s, price = %s, des = %s, stock = %s 
                WHERE id = %s AND user_id = %s
            """, (name, code, price, description, stock, id, session['user_id']))
        
        mysql.connection.commit()

        flash("Product updated successfully!")
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


if __name__ == '__main__':
    app.run(debug=True)
