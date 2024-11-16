from flask import Flask, request, render_template, redirect, url_for, session
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
    return render_template('add_product.html', success=success)


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
        return "Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed."

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(
            "INSERT INTO product (user_id, code, name, price, des, stock, image) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (session['user_id'], code, name,price, description, stock, image_path)
        )
        mysql.connection.commit()

        # Redirect back to the add product form with a success flag
        return redirect(url_for('products', success=True))
    except MySQLdb.Error as e:
        mysql.connection.rollback()
        return f"Failed to add product: {e}"
    finally:
        cursor.close()

# Route to fetch and display all products
@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))  # Redirect to login if not logged in
    print(session.get('user_id'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM product WHERE user_id = %s", (session['user_id'],))
        products = cursor.fetchall()
        
        print(products)

        return render_template('products.html', products=products)
    except MySQLdb.Error as e:
        return f"Failed to fetch products: {e}"
    finally:
        cursor.close()


# Prevent back button after logout
@app.after_request
def prevent_back_on_logout(response):
    if request.endpoint == 'logout':
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create upload folder if it doesn't exist
    app.run(debug=True, host='127.0.0.1', port=5000)
