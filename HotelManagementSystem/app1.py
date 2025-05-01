import sqlite3
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL



app = Flask(__name__, static_folder='static')

# Set a secret key for session management
app.secret_key = 'secret_key'

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hotelmanagementsystem'

mysql = MySQL(app)

# Centralized login check function
def check_login():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return None

# Route for login page (GET and POST)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate username and password with the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT username, password FROM login WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and password == user[1]:  # Check if password matches
            session['username'] = user[0]  # Store username in session
            return redirect(url_for('hotel'))  # Redirect to hotel page
        else:
            flash('Invalid username or password', 'error')  # Flash error message
            return redirect(url_for('login'))  # Redirect to login page again

    return render_template('login2.html')  # Render login page if GET request


def get_db_connection():
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database (run this once to create the table)
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            floor TEXT NOT NULL,
            roomNo TEXT NOT NULL PRIMARY KEY,
            roomType TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

# Fetch all rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    return jsonify([dict(room) for room in rooms])

# Add a new room
@app.route('/rooms', methods=['POST'])
def add_room():
    room = request.get_json()
    floor = room.get('floor')
    roomNo = room.get('roomNo')
    roomType = room.get('roomType')

    if not floor or not roomNo or not roomType:
        return jsonify({'message': 'All fields are required'}), 400

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO rooms (floor, roomNo, roomType) VALUES (?, ?, ?)', 
                     (floor, roomNo, roomType))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Room added successfully'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Room already exists'}), 400

# Update an existing room
@app.route('/rooms/<floor>/<roomNo>', methods=['PUT'])
def update_room(floor, roomNo):
    room = request.get_json()
    roomType = room.get('roomType')

    if not roomType:
        return jsonify({'message': 'Room Type is required'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE rooms SET roomType = ? WHERE floor = ? AND roomNo = ?',
                 (roomType, floor, roomNo))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Room updated successfully'}), 200

# Delete a room
@app.route('/rooms/<floor>/<roomNo>', methods=['DELETE'])
def delete_room(floor, roomNo):
    conn = get_db_connection()
    conn.execute('DELETE FROM rooms WHERE floor = ? AND roomNo = ?', (floor, roomNo))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Room deleted successfully'}), 200


# Route for logout (POST)
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove username from session (logout)
    flash("You have successfully logged out.", "success")
    return redirect(url_for('login'))  # Redirect to login page after logout

# Route for the hotel section
@app.route('/hotel')
def hotel():
    login_check = check_login()
    if login_check:
        return login_check
    return render_template('hotel.html')

# Route for the customer section
@app.route('/customer')
def customer():
    login_check = check_login()
    if login_check:
        return login_check
    return render_template('customer.html')

# Route for the room section
@app.route('/room')
def room():
    login_check = check_login()
    if login_check:
        return login_check
    return render_template('room.html')

# Route for the details section
@app.route('/details')
def details():
    login_check = check_login()
    if login_check:
        return login_check
    return render_template('detail.html')


# API to get available rooms based on room type
# Fetch distinct room types and available rooms for bookings
@app.route('/api/bookings', methods=['GET', 'POST'])
def manage_bookings():
    if request.method == 'GET':
        # Fetch all bookings
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM bookings")
        rows = cur.fetchall()

        bookings = [
            {
                'id': row[0],
                'contact': row[1],
                'checkin': row[2],
                'checkout': row[3],
                'roomType': row[4],
                'availableRoom': row[5],
                'meal': row[6],
                'noOfDays': row[7],
                'paidTax': row[8],
                'subTotal': row[9],
                'totalCost': row[10]
            } for row in rows
        ]

        # Fetch distinct room types from 'details' table
        cur.execute("SELECT DISTINCT roomType FROM details")  # Fetch distinct room types
        room_types = cur.fetchall()
        
        # To improve performance, you can fetch available rooms for each room type
        available_rooms_by_type = {}
        for room_type in room_types:
            cur.execute("SELECT roomNo FROM details WHERE roomType = %s", (room_type[0],))
            available_rooms = cur.fetchall()
            available_rooms_by_type[room_type[0]] = [room[0] for room in available_rooms]

        cur.close()  # Close the cursor once after all queries

        return jsonify({
            'bookings': bookings,
            'roomTypes': [room[0] for room in room_types],
            'availableRooms': available_rooms_by_type
        })

    if request.method == 'POST':
        # Add a new booking
        booking = request.get_json()
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO bookings (contact, checkin, checkout, roomType, availableRoom, meal, 
                                       noOfDays, paidTax, subTotal, totalCost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (booking['contact'], booking['checkin'], booking['checkout'], booking['roomType'],
                  booking['availableRoom'], booking['meal'], booking['noOfDays'], booking['paidTax'],
                  booking['subTotal'], booking['totalCost']))
            mysql.connection.commit()
            cur.close()  # Close cursor after commit
            return jsonify({'message': 'Booking added successfully'}), 201
        except Exception as e:
            cur.close()  # Ensure the cursor is closed in case of an error
            return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/available_rooms', methods=['GET'])
def get_available_rooms():
    room_type = request.args.get('roomType')
    
    if not room_type:
        return jsonify({'message': 'Room type is required'}), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT roomNo FROM details WHERE roomType = %s", (room_type,))
    available_rooms = cur.fetchall()
    cur.close()  # Close the cursor after the query

    return jsonify([room[0] for room in available_rooms])  # Return available rooms



# API for managing customers (GET, POST, PUT, DELETE)
@app.route('/customers', methods=['GET', 'POST', 'PUT', 'DELETE'])
def customers():
    if request.method == 'POST':
        # Create a new customer (POST)
        customer = request.get_json()
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO customers (customerName, phone, email, address, id, gender, nationality)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (customer['customerName'], customer['phone'], customer['email'], customer['address'],
                  customer['id'], customer['gender'], customer['nationality']))
            mysql.connection.commit()
            cur.close()
            return jsonify({'message': 'Customer added successfully'}), 201
        except Exception as e:
            cur.close()
            return jsonify({'message': f'Error: {str(e)}'}), 500

    elif request.method == 'PUT':
        # Update a customer (PUT)
        customer = request.get_json()
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                UPDATE customers 
                SET customerName=%s, phone=%s, email=%s, address=%s, id=%s, gender=%s, nationality=%s
                WHERE customerRef=%s
            """, (customer['customerName'], customer['phone'], customer['email'], customer['address'],
                  customer['id'], customer['gender'], customer['nationality'], customer['customerRef']))
            mysql.connection.commit()
            cur.close()
            return jsonify({'message': 'Customer updated successfully'}), 200
        except Exception as e:
            cur.close()
            return jsonify({'message': f'Error: {str(e)}'}), 500

    elif request.method == 'DELETE':
        # Delete a customer (DELETE)
        customer_ref = request.args.get('customerRef')
        cur = mysql.connection.cursor()
        try:
            cur.execute("DELETE FROM customers WHERE customerRef = %s", (customer_ref,))
            mysql.connection.commit()
            cur.close()
            return jsonify({'message': 'Customer deleted successfully'}), 200
        except Exception as e:
            cur.close()
            return jsonify({'message': f'Error: {str(e)}'}), 500

    elif request.method == 'GET':
        # Get all customers (GET)
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM customers")
            rows = cur.fetchall()
            cur.close()

            customers = [
                {
                    'customerRef': row[0],
                    'customerName': row[1],
                    'phone': row[2],
                    'email': row[3],
                    'address': row[4],
                    'id': row[5],
                    'gender': row[6],
                    'nationality': row[7]
                } for row in rows
            ]
            return jsonify(customers)
        except Exception as e:
            cur.close()
            return jsonify({'message': f'Error: {str(e)}'}), 500


# Search route for customers (GET)
@app.route('/customers/search', methods=['GET'])
def search_customers():
    search_by = request.args.get('searchBy')  # This should be 'ref' or 'phone'
    search_value = request.args.get('searchValue')  # The actual search term entered by the user

    if search_by not in ['ref', 'phone']:
        return jsonify({'message': 'Invalid search parameter'}), 400

    query = f"SELECT * FROM customers WHERE {search_by} LIKE %s"
    cur = mysql.connection.cursor()
    try:
        cur.execute(query, (f'%{search_value}%',))  # Use LIKE to find partial matches
        rows = cur.fetchall()
        cur.close()

        customers = [
            {
                'customerRef': row[0],
                'customerName': row[1],
                'phone': row[2],
                'email': row[3],
                'address': row[4],
                'id': row[5],
                'gender': row[6],
                'nationality': row[7]
            } for row in rows
        ]

        if not customers:
            return jsonify({'message': 'No customers found'}), 404
        
        return jsonify(customers)
    except Exception as e:
        cur.close()
        return jsonify({'message': f'Error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
