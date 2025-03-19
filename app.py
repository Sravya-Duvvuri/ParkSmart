import flask
from flask import Flask, request, redirect, url_for, session, render_template, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_KEY"

# 1) Create the database and tables if they don't exist
def create_db_and_table():
    try:
        # Connect to MySQL (without specifying a database)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Negligence@13"
        )
        cursor = conn.cursor()

        # Create the database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS my_app_db")
        cursor.execute("USE my_app_db")

        # Create Users Table
        create_users_table = """
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
        cursor.execute(create_users_table)

        # Create Payments Table
        create_payments_table = """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100),
            amount DECIMAL(10,2),
            payment_method VARCHAR(50),
            promo_code VARCHAR(20),
            final_amount DECIMAL(10,2),
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES tbl_users(email) ON DELETE CASCADE
        );
        """
        cursor.execute(create_payments_table)

        # Create Vehicles Table using user's email as foreign key
        create_vehicles_table = """
        CREATE TABLE IF NOT EXISTS tbl_vehicles (
            vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(100),
            vehicle_number VARCHAR(50),
            vehicle_model VARCHAR(100),
            vehicle_color VARCHAR(50),
            registration_year INT,
            FOREIGN KEY (user_email) REFERENCES tbl_users(email) ON DELETE CASCADE
        );
        """
        cursor.execute(create_vehicles_table)

        # Create Wallets Table with default balance of 1000
        create_wallets_table = """
        CREATE TABLE IF NOT EXISTS tbl_wallets (
            wallet_id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(100),
            balance DECIMAL(10,2) DEFAULT 1000,
            FOREIGN KEY (user_email) REFERENCES tbl_users(email) ON DELETE CASCADE
        );
        """
        cursor.execute(create_wallets_table)

        conn.commit()
        cursor.close()
        conn.close()
        print("Database and tables created (if they did not exist).")
    except Error as e:
        print("Error creating database or tables:", e)

# 2) Helper function to get a connection to the database
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
    return redirect(url_for("register"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        licence = request.form.get("licence")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")
        phone = request.form.get("phone")
        dob = request.form.get("dob")

        if password != confirm_password:
            return "Passwords do not match. <a href='/register'>Try again</a>"

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

            # Automatically register a wallet with default balance 1000
            insert_wallet_query = "INSERT INTO tbl_wallets (user_email) VALUES (%s)"
            cursor.execute(insert_wallet_query, (email,))
            conn.commit()

            cursor.close()
            conn.close()
            return redirect(url_for("login"))
        except Error as e:
            return f"Error inserting data: {e}"
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed!"
        try:
            cursor = conn.cursor(dictionary=True)
            select_query = "SELECT * FROM tbl_users WHERE email = %s AND password = %s"
            cursor.execute(select_query, (email, password))
            user = cursor.fetchone()
            if user:
                session["user_id"] = user["id"]
                session["email"] = user["email"]

                # Ensure a wallet record exists for this user
                cursor2 = conn.cursor()
                select_wallet_query = "SELECT * FROM tbl_wallets WHERE user_email = %s"
                cursor2.execute(select_wallet_query, (email,))
                wallet = cursor2.fetchone()
                if wallet is None:
                    insert_wallet_query = "INSERT INTO tbl_wallets (user_email) VALUES (%s)"
                    cursor2.execute(insert_wallet_query, (email,))
                    conn.commit()
                cursor2.close()

                cursor.close()
                conn.close()
                return redirect(url_for("page1"))
            else:
                cursor.close()
                conn.close()
                return redirect(url_for("login"))
        except Error as e:
            return f"Error during login: {e}"
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

@app.route("/navigation")
def navigation():
    return render_template("navigation.html")

# Note: If you intended to have a detection page, add a route for it.
# For example, to fix the broken link in page1.html, you can add:
@app.route("/detection")
def detection():
    return render_template("detection.html")

@app.route("/detection2")
def detection2():
    return render_template("detection2.html")

@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/register_vehicle", methods=["GET", "POST"])
def register_vehicle():
    if request.method == "POST":
        user_email = session.get("email")
        vehicle_number = request.form.get("vehicle_number")
        vehicle_model = request.form.get("vehicle_model")
        vehicle_color = request.form.get("vehicle_color")
        registration_year = request.form.get("registration_year")
        if not user_email:
            return "User not logged in. Please login first."
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed!"
        try:
            cursor = conn.cursor()
            insert_query = """
            INSERT INTO tbl_vehicles (user_email, vehicle_number, vehicle_model, vehicle_color, registration_year)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (user_email, vehicle_number, vehicle_model, vehicle_color, registration_year))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("page1"))
        except Error as e:
            return f"Error inserting vehicle data: {e}"
    return render_template("register_vehicle.html")

# Endpoint: Get registered vehicles for the logged-in user
@app.route("/get_user_vehicles")
def get_user_vehicles():
    if "email" not in session:
        return jsonify({"vehicles": []})
    email = session["email"]
    conn = get_db_connection()
    if conn is None:
        return jsonify({"vehicles": []})
    cursor = conn.cursor()
    cursor.execute("SELECT vehicle_number FROM tbl_vehicles WHERE user_email = %s", (email,))
    vehicles = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify({"vehicles": vehicles})

# Endpoint: Get current wallet balance for the logged-in user
@app.route("/get_wallet_balance")
def get_wallet_balance():
    if "email" not in session:
        return jsonify({"balance": 0})
    email = session["email"]
    conn = get_db_connection()
    if conn is None:
        return jsonify({"balance": 0})
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM tbl_wallets WHERE user_email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"balance": result[0] if result else 0})

# Endpoint: Process wallet payment – deduct the amount and record the transaction
@app.route("/process_wallet_payment", methods=["POST"])
def process_wallet_payment():
    if "email" not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401
    data = request.get_json()
    try:
        final_amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount provided"}), 400
    payment_method = data.get("payment_method")
    promo_code = data.get("promo_code")
    email = session["email"]

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM tbl_wallets WHERE user_email = %s", (email,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"success": False, "error": "Wallet record not found"}), 400
        current_balance = float(result[0])
        if current_balance < final_amount:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Insufficient wallet balance"}), 400

        cursor.execute("UPDATE tbl_wallets SET balance = balance - %s WHERE user_email = %s", (final_amount, email))
        conn.commit()

        cursor.execute(
            "INSERT INTO payments (email, amount, payment_method, promo_code, final_amount) VALUES (%s, %s, %s, %s, %s)",
            (email, final_amount, payment_method, promo_code, final_amount)
        )
        conn.commit()

        cursor.execute("SELECT balance FROM tbl_wallets WHERE user_email = %s", (email,))
        updated_balance = float(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return jsonify({"success": True, "remaining_balance": updated_balance})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    create_db_and_table()
    app.run(debug=True)
