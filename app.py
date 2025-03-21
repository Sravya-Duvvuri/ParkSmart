import flask
from flask import Flask, request, redirect, url_for, session, render_template, jsonify
import mysql.connector
from mysql.connector import Error
import datetime
import random  # Needed for the init_parking_slots endpoint

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

        # Create Admins Table
        create_admins_table = """
        CREATE TABLE IF NOT EXISTS tbl_admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100) UNIQUE,
            password VARCHAR(255)
        );
        """
        cursor.execute(create_admins_table)

        # Create Transactions Table
        create_transactions_table = """
        CREATE TABLE IF NOT EXISTS tbl_transactions (
            transaction_id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(100),
            start_time DATETIME,
            end_time DATETIME,
            transaction_mode VARCHAR(50),
            amount DECIMAL(10,2),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES tbl_users(email) ON DELETE CASCADE
        );
        """
        cursor.execute(create_transactions_table)

        # Create UPI Transactions Table
        create_upi_transactions = """
        CREATE TABLE IF NOT EXISTS tbl_upi_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id INT,
            upi_id VARCHAR(100),
            promo_code VARCHAR(20),
            FOREIGN KEY (transaction_id) REFERENCES tbl_transactions(transaction_id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_upi_transactions)

        # Create Wallet Transactions Table
        create_wallet_transactions = """
        CREATE TABLE IF NOT EXISTS tbl_wallet_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id INT,
            payment_method VARCHAR(50),
            promo_code VARCHAR(20),
            FOREIGN KEY (transaction_id) REFERENCES tbl_transactions(transaction_id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_wallet_transactions)

        # Create Credit Transactions Table
        create_credit_transactions = """
        CREATE TABLE IF NOT EXISTS tbl_credit_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id INT,
            card_number VARCHAR(20),
            card_holder VARCHAR(100),
            expiry_date VARCHAR(10),
            promo_code VARCHAR(20),
            FOREIGN KEY (transaction_id) REFERENCES tbl_transactions(transaction_id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_credit_transactions)

        # Create Debit Transactions Table
        create_debit_transactions = """
        CREATE TABLE IF NOT EXISTS tbl_debit_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id INT,
            card_number VARCHAR(20),
            card_holder VARCHAR(100),
            expiry_date VARCHAR(10),
            promo_code VARCHAR(20),
            FOREIGN KEY (transaction_id) REFERENCES tbl_transactions(transaction_id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_debit_transactions)

        # Create Login History Table
        create_login_history_table = """
        CREATE TABLE IF NOT EXISTS tbl_login_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(100),
            login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(50)
        );
        """
        cursor.execute(create_login_history_table)

        # Create Parking Slots Table
        create_parking_slots_table = """
        CREATE TABLE IF NOT EXISTS tbl_parking_slots (
            slot_id INT AUTO_INCREMENT PRIMARY KEY,
            slot_name VARCHAR(50) UNIQUE,
            lat DECIMAL(10,6),
            lng DECIMAL(10,6)
        );
        """
        cursor.execute(create_parking_slots_table)

        # Create Slot Reservations Table
        create_slot_res_table = """
        CREATE TABLE IF NOT EXISTS tbl_slot_reservations (
            reservation_id INT AUTO_INCREMENT PRIMARY KEY,
            slot_id INT,
            user_email VARCHAR(100),
            start_time DATETIME,
            end_time DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (slot_id) REFERENCES tbl_parking_slots(slot_id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_slot_res_table)

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
            
            # First, check if the credentials match an admin record.
            select_admin_query = "SELECT * FROM tbl_admins WHERE email = %s AND password = %s"
            cursor.execute(select_admin_query, (email, password))
            admin = cursor.fetchone()
            if admin:
                session["admin_id"] = admin["id"]
                session["email"] = admin["email"]
                # Insert login history for admin
                user_ip = request.remote_addr
                insert_login_history = "INSERT INTO tbl_login_history (user_email, ip_address) VALUES (%s, %s)"
                cursor.execute(insert_login_history, (email, user_ip))
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for("admin_home"))
            
            # Otherwise, check if they match a regular user.
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

                # Insert login history record for the user
                user_ip = request.remote_addr
                insert_login_history = "INSERT INTO tbl_login_history (user_email, ip_address) VALUES (%s, %s)"
                cursor.execute(insert_login_history, (email, user_ip))
                conn.commit()

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

@app.route("/wallet")
def wallet():
    return render_template("wallet.html")

@app.route("/navigation")
def navigation():
    return render_template("navigation.html")

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

        # Update wallet balance
        cursor.execute("UPDATE tbl_wallets SET balance = balance - %s WHERE user_email = %s", (final_amount, email))
        conn.commit()

        # Record payment in payments table
        cursor.execute(
            "INSERT INTO payments (email, amount, payment_method, promo_code, final_amount) VALUES (%s, %s, %s, %s, %s)",
            (email, final_amount, payment_method, promo_code, final_amount)
        )
        conn.commit()

        # Insert a record into the main transactions table
        start_time = data.get("start_time")  # Expect these to be passed from the client
        end_time = data.get("end_time")
        transaction_mode = "Wallet"
        status = "Successful"
        insert_transaction = """
            INSERT INTO tbl_transactions (user_email, start_time, end_time, transaction_mode, amount, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_transaction, (email, start_time, end_time, transaction_mode, final_amount, status))
        conn.commit()
        transaction_id = cursor.lastrowid  # Get the ID of the newly inserted transaction

        # Insert record into wallet_transactions table
        insert_wallet_transaction = """
            INSERT INTO tbl_wallet_transactions (transaction_id, payment_method, promo_code)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_wallet_transaction, (transaction_id, payment_method, promo_code))
        conn.commit()

        # Return updated wallet balance
        cursor.execute("SELECT balance FROM tbl_wallets WHERE user_email = %s", (email,))
        updated_balance = float(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return jsonify({"success": True, "remaining_balance": updated_balance})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/process_debit_payment", methods=["POST"])
def process_debit_payment():
    if "email" not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401
    data = request.get_json()
    try:
        final_amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount provided"}), 400

    card_number = data.get("card_number")
    card_holder = data.get("card_holder")
    expiry_date = data.get("expiry_date")
    promo_code = data.get("promo_code")
    start_time = data.get("start_time")  # passed from the client
    end_time = data.get("end_time")      # passed from the client
    email = session["email"]

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor()
        transaction_mode = "Debit Card"
        status = "Successful"
        insert_transaction = """
            INSERT INTO tbl_transactions (user_email, start_time, end_time, transaction_mode, amount, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_transaction, (email, start_time, end_time, transaction_mode, final_amount, status))
        conn.commit()
        transaction_id = cursor.lastrowid

        insert_debit_transaction = """
            INSERT INTO tbl_debit_transactions (transaction_id, card_number, card_holder, expiry_date, promo_code)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_debit_transaction, (transaction_id, card_number, card_holder, expiry_date, promo_code))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/process_credit_payment", methods=["POST"])
def process_credit_payment():
    if "email" not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401
    data = request.get_json()
    try:
        final_amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount provided"}), 400

    card_number = data.get("card_number")
    card_holder = data.get("card_holder")
    expiry_date = data.get("expiry_date")
    promo_code = data.get("promo_code")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    email = session["email"]

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor()
        transaction_mode = "Credit Card"
        status = "Successful"
        insert_transaction = """
            INSERT INTO tbl_transactions (user_email, start_time, end_time, transaction_mode, amount, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_transaction, (email, start_time, end_time, transaction_mode, final_amount, status))
        conn.commit()
        transaction_id = cursor.lastrowid

        insert_credit = """
            INSERT INTO tbl_credit_transactions (transaction_id, card_number, card_holder, expiry_date, promo_code)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_credit, (transaction_id, card_number, card_holder, expiry_date, promo_code))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/process_upi_payment", methods=["POST"])
def process_upi_payment():
    if "email" not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401
    data = request.get_json()
    try:
        final_amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount provided"}), 400

    upi_id = data.get("upi_id")
    promo_code = data.get("promo_code")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    email = session["email"]

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor()
        transaction_mode = "UPI"
        status = "Successful"
        insert_transaction = """
            INSERT INTO tbl_transactions (user_email, start_time, end_time, transaction_mode, amount, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_transaction, (email, start_time, end_time, transaction_mode, final_amount, status))
        conn.commit()
        transaction_id = cursor.lastrowid

        insert_upi = """
            INSERT INTO tbl_upi_transactions (transaction_id, upi_id, promo_code)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_upi, (transaction_id, upi_id, promo_code))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/init_parking_slots")
def init_parking_slots():
    """Seed 10 random slots if none exist."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as cnt FROM tbl_parking_slots")
        row = cursor.fetchone()
        if row["cnt"] == 0:
            base_lat, base_lng = 11.0168, 76.9558
            for i in range(1, 11):
                lat = base_lat + random.uniform(-0.01, 0.01)
                lng = base_lng + random.uniform(-0.01, 0.01)
                slot_name = f"Slot {i}"
                insert_q = "INSERT INTO tbl_parking_slots (slot_name, lat, lng) VALUES (%s, %s, %s)"
                cursor.execute(insert_q, (slot_name, lat, lng))
            conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_parking_slots", methods=["GET"])
def get_parking_slots():
    """Return all slots from tbl_parking_slots."""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT slot_id, slot_name, lat, lng
        FROM tbl_parking_slots
        ORDER BY slot_id
        """
        cursor.execute(query)
        slots = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(slots)
    except Error:
        return jsonify([])

@app.route("/get_slot_reservations", methods=["GET"])
def get_slot_reservations():
    """Return all reservations from tbl_slot_reservations."""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT reservation_id, slot_id, user_email, start_time, end_time, created_at
        FROM tbl_slot_reservations
        ORDER BY start_time
        """
        cursor.execute(query)
        res = cursor.fetchall()
        for r in res:
            if isinstance(r["start_time"], datetime.datetime):
                r["start_time"] = r["start_time"].isoformat()
            if isinstance(r["end_time"], datetime.datetime):
                r["end_time"] = r["end_time"].isoformat()
            if isinstance(r["created_at"], datetime.datetime):
                r["created_at"] = r["created_at"].isoformat()
        cursor.close()
        conn.close()
        return jsonify(res)
    except Error as e:
        print("Error fetching slot reservations:", e)
        return jsonify([])

@app.route("/reserve_slot", methods=["POST"])
def reserve_slot():
    """Insert a new reservation if no overlap for that slot/time range."""
    if "email" not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401
    data = request.get_json()
    slot_id = data.get("slot_id")
    reserved_from = data.get("reserved_from")  # "YYYY-MM-DD HH:MM:SS"
    reserved_to = data.get("reserved_to")
    email = session["email"]

    if not slot_id or not reserved_from or not reserved_to:
        return jsonify({"success": False, "error": "Missing reservation details"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor()

        # Overlap check for the same slot
        overlap_q = """
        SELECT reservation_id FROM tbl_slot_reservations
        WHERE slot_id = %s
          AND (start_time < %s AND end_time > %s)
        """
        cursor.execute(overlap_q, (slot_id, reserved_to, reserved_from))
        overlap = cursor.fetchone()
        if overlap:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "This slot is already reserved for that time range."}), 400

        # If you also want to prevent the user from double-booking themselves:
        user_overlap_q = """
        SELECT reservation_id FROM tbl_slot_reservations
        WHERE user_email = %s
          AND (start_time < %s AND end_time > %s)
        """
        cursor.execute(user_overlap_q, (email, reserved_to, reserved_from))
        user_overlap = cursor.fetchone()
        if user_overlap:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "You already have an overlapping reservation."}), 400

        # Insert new reservation
        insert_q = """
        INSERT INTO tbl_slot_reservations (slot_id, user_email, start_time, end_time)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_q, (slot_id, email, reserved_from, reserved_to))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------
# Admin Routes
# -------------------------

@app.route("/admin_home")
def admin_home():
    if "admin_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_home-page.html")

@app.route("/admin_tracking")
def admin_tracking():
    if "admin_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_tracking.html")

@app.route("/admin_datainsights")
def admin_datainsights():
    if "admin_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_datainsights.html")

@app.route("/admin_dataexport")
def admin_dataexport():
    if "admin_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_dataexport.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")

@app.route("/admin_navigation")
def admin_navigation():
    if "admin_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_navigation.html")

@app.route("/get_transactions", methods=["GET"])
def get_transactions():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT transaction_id, user_email, 
                   COALESCE(start_time, created_at) AS start_time, 
                   end_time, transaction_mode, amount, status, created_at
            FROM tbl_transactions
            ORDER BY start_time DESC
        """
        cursor.execute(query)
        transactions = cursor.fetchall()
        
        for tx in transactions:
            if not tx.get('start_time'):
                tx['start_time'] = tx['created_at']
            if isinstance(tx.get('start_time'), datetime.datetime):
                tx['start_time'] = tx['start_time'].isoformat()
            if tx.get('end_time') and isinstance(tx.get('end_time'), datetime.datetime):
                tx['end_time'] = tx['end_time'].isoformat()
            if isinstance(tx.get('created_at'), datetime.datetime):
                tx['created_at'] = tx['created_at'].isoformat()
                
        print("Fetched transactions:", transactions)
        cursor.close()
        conn.close()
        return jsonify(transactions)
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin_get_users", methods=["GET"])
def admin_get_users():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name, email, 'User' AS role FROM tbl_users"
        cursor.execute(query)
        users = cursor.fetchall()
        query_admin = "SELECT id, email, 'Admin' AS role FROM tbl_admins"
        cursor.execute(query_admin)
        admins = cursor.fetchall()
        cursor.close()
        conn.close()
        all_users = admins + users
        return jsonify(all_users)
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin_delete_user", methods=["POST"])
def admin_delete_user():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "User ID not provided"}), 400
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor()
        query = "DELETE FROM tbl_users WHERE id = %s"
        cursor.execute(query, (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route("/admin_get_logins", methods=["GET"])
def admin_get_logins():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, user_email, login_time, ip_address
            FROM tbl_login_history
            ORDER BY login_time DESC
        """
        cursor.execute(query)
        logins = cursor.fetchall()
        for login in logins:
            if isinstance(login.get('login_time'), datetime.datetime):
                login['login_time'] = login['login_time'].isoformat()
        cursor.close()
        conn.close()
        return jsonify(logins)
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route("/admin_toggle_2fa", methods=["POST"])
def admin_toggle_2fa():
    data = request.get_json()
    enabled = data.get("enabled")
    return jsonify({"success": True, "2fa_enabled": enabled})

if __name__ == "__main__":
    create_db_and_table()
    app.run(debug=True)
