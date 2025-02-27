from flask import Flask, request, redirect, url_for, session, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_KEY"

# 1) Create the database and table if they don't exist
def create_db_and_table():
    try:
        # Connect to MySQL (no specific database yet)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Negligence@13"
        )
        cursor = conn.cursor()

        # Create a new database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS my_app_db")

        # Switch to the new database
        cursor.execute("USE my_app_db")

        # Create a new table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tbl_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            licence VARCHAR(50),
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password VARCHAR(255),
            phone VARCHAR(15),
            dob DATE
        );
        """
        cursor.execute(create_table_query)
        conn.commit()

        cursor.close()
        conn.close()
        print("Database and table created (if they did not exist).")
    except Error as e:
        print("Error creating database or table:", e)

# 2) A helper function to get a connection **to** that new database
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Negligence@13",
            database="my_app_db"
        )
        return conn
    except Error as e:
        print("Error connecting to MySQL:", e)
        return None

# 3) Flask Routes

@app.route("/")
def home():
    # Redirect to the register page by default
    return redirect(url_for("register"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Retrieve data from form fields in register.html
        licence = request.form.get("licence")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")
        phone = request.form.get("phone")
        dob = request.form.get("dob")

        # Simple server-side check if passwords match
        if password != confirm_password:
            return "Passwords do not match. <a href='/register'>Try again</a>"

        # Insert into MySQL
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed!"
        try:
            cursor = conn.cursor()
            insert_query = """
            INSERT INTO tbl_users (licence, name, email, password, phone, dob)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (licence, name, email, password, phone, dob))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for("login"))
        except Error as e:
            return f"Error inserting data: {e}"

    # On GET, render your existing register.html
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Retrieve data from form fields in login.html
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        if conn is None:
            return "Database connection failed!"
        try:
            cursor = conn.cursor(dictionary=True)
            select_query = """
            SELECT * FROM tbl_users
            WHERE email = %s AND password = %s
            """
            cursor.execute(select_query, (email, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                # User authenticated -> store session data
                session["user_id"] = user["id"]
                return redirect(url_for("page1"))
            else:
                return redirect(url_for("login"))
        except Error as e:
            return f"Error during login: {e}"

    # On GET, render your existing login.html
    return render_template("login.html")

@app.route("/page1")
def page1():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("page1.html")

@app.route("/credit")
def credit():
    return render_template("credit.html")

@app.route("/debit")
def debit():
    return render_template("debit.html")

@app.route("/digitalwallet")
def digitalwallet():
    return render_template("digitalwallet.html")

@app.route("/payment")
def payment():
    return render_template("payment.html")

@app.route("/upi")
def upi():
    return render_template("upi.html")

@app.route("/upipay")
def upipay():
    return render_template("UPIpay.html")

@app.route("/wallet")
def wallet():
    return render_template("wallet.html")

# 4) Start the app
if __name__ == "__main__":
    # Create DB & table if not exist
    create_db_and_table()
    app.run(debug=True)
