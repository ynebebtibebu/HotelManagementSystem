import sqlite3
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL

# Initialize Flask app
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
@app.route('/room2')
def room2():
    return render_template('userroom.html')

@app.route('/register.html')
def register():
    return render_template('register.html')

@app.route('/payment.html')
def payment():
    return render_template('payment.html')
@app.route('/success.html')
def success():
    return render_template('success.html')


# MySQL Room Management Routes

# Fetch all rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM details')  # Ensure 'details' table exists
        rooms = cur.fetchall()
        cur.close()

        # Convert rows to dictionaries
        room_list = [
            {'floor': room[0], 'roomNo': room[1], 'roomType': room[2]} for room in rooms
        ]

        # Extract unique room types
        room_types = list(set([room[2] for room in rooms]))

        return jsonify({'roomTypes': room_types, 'rooms': room_list})

    except Exception as e:
        return jsonify({'message': f'Error fetching rooms: {str(e)}'}), 500
    
    

@app.route('/rooms/available_rooms', methods=['GET'])
def get_available_rooms():
    room_type = request.args.get('roomType')  # Get selected room type from the query parameter

    if not room_type:
        return jsonify({'message': 'Room Type is required'}), 400

    try:
        cur = mysql.connection.cursor()
        # Fetch available rooms by roomType (assuming 'roomType' is stored in your table)
        cur.execute('SELECT floor, roomNo, roomType FROM details WHERE roomType = %s', (room_type,))
        rooms = cur.fetchall()
        cur.close()

        # Convert rooms to dictionaries
        available_rooms = [
            {'floor': room[0], 'roomNo': room[1], 'roomType': room[2]} for room in rooms
        ]
        
        return jsonify(available_rooms)

    except Exception as e:
        return jsonify({'message': f'Error fetching available rooms: {str(e)}'}), 500
@app.route('/api/bookings', methods=['POST'])
def add_booking():
    try:
        booking = request.get_json()
        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO bookings (contact, checkin, checkout, roomType, availableRoom, meal, noOfDays, paidTax, subTotal, totalCost)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                booking['contact'],
                booking['checkin'],
                booking['checkout'],
                booking['roomType'],
                booking['availableRoom'],
                booking['meal'],
                booking['noOfDays'],
                booking['paidTax'],
                booking['subTotal'],
                booking['totalCost'],
            ),
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Booking added successfully'}), 201

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    try:
        booking = request.get_json()
        cur = mysql.connection.cursor()

        cur.execute(
            """
            UPDATE bookings
            SET contact = %s, checkin = %s, checkout = %s, roomType = %s, availableRoom = %s, meal = %s, noOfDays = %s, paidTax = %s, subTotal = %s, totalCost = %s
            WHERE id = %s
            """,
            (
                booking['contact'],
                booking['checkin'],
                booking['checkout'],
                booking['roomType'],
                booking['availableRoom'],
                booking['meal'],
                booking['noOfDays'],
                booking['paidTax'],
                booking['subTotal'],
                booking['totalCost'],
                booking_id,
            ),
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Booking updated successfully'}), 200

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
    

@app.route('/api/bookings/<int:id>', methods=['DELETE'])
def delete_booking(id):
    cur = mysql.connection.cursor()
    try:
        # Use the 'id' from the route parameter
        cur.execute("DELETE FROM bookings WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Booking deleted successfully'}), 200
    except Exception as e:
        cur.close()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/bookings', methods=['GET'])
def get_all_bookings():
    # Get all customers (GET)
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM bookings")
            rows = cur.fetchall()
            cur.close()

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
                'totalCost': row[10],
            }
            for row in rows
        ]
            return jsonify(bookings), 200
        except Exception as e:
            cur.close()
            return jsonify({'message': f'Error: {str(e)}'}), 500




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
        

@app.route('/detail', methods=['GET', 'POST', 'PUT', 'DELETE'])
def detail():
    cur = mysql.connection.cursor()

    try:
        if request.method == 'POST':
            room = request.get_json()
            cur.execute("INSERT INTO details (floor, roomNo, roomType) VALUES (%s, %s, %s)", (room['floor'], room['roomNo'], room['roomType']))
            mysql.connection.commit()
            return jsonify({'message': 'Room added successfully'}), 201

        elif request.method == 'PUT':
            room = request.get_json()
            cur.execute("UPDATE details SET floor=%s, roomType=%s WHERE roomNo=%s", (room['floor'], room['roomType'], room['roomNo']))
            mysql.connection.commit()
            return jsonify({'message': 'Room updated successfully'}), 200

        elif request.method == 'DELETE':
            room_no = request.args.get('roomNo')
            if not room_no:
                return jsonify({'message': 'Room number is required for deletion'}), 400

            cur.execute("DELETE FROM details WHERE roomNo = %s", (room_no,))
            mysql.connection.commit()
            return jsonify({'message': 'Room deleted successfully'}), 200

        elif request.method == 'GET':
            cur.execute("SELECT * FROM details")
            rows = cur.fetchall()
            rooms = [{'floor': row[0], 'roomNo': row[1], 'roomType': row[2]} for row in rows]
            return jsonify(rooms), 200

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

    finally:
        cur.close()


        


@app.route('/customers/search', methods=['GET'])
def search_customers():
    search_by = request.args.get('searchBy')  # 'ref' or 'phone'
    search_value = request.args.get('searchValue')  # The actual search term entered by the user

    print(f"Search by: {search_by}, Search value: {search_value}")  # Debugging print

    # Validate search parameter
    if search_by not in ['ref', 'phone']:
        return jsonify({'message': 'Invalid search parameter'}), 400

    # Adjust query based on the search parameter
    if search_by == 'phone':
        query = "SELECT * FROM customers WHERE phone LIKE %s"  # Use LIKE for phone numbers
        search_value = f'%{search_value}%'  # Add wildcards for LIKE
    else:
        query = "SELECT * FROM customers WHERE customerRef = %s"  # Exact match for customerRef
        search_value = search_value  # No wildcards for customerRef

    cur = mysql.connection.cursor()

    try:
        cur.execute(query, (search_value,))
        rows = cur.fetchall()
        cur.close()

        if not rows:
            return jsonify({'message': 'No customers found'}), 404

        # Format the data into a list of dictionaries
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

        return jsonify(customers)  # Return the list of customers as JSON
    except Exception as e:
        cur.close()
        print(f"Error in search query: {str(e)}")  # Debugging print
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/fetch_customer', methods=['GET'])
def fetch_customer():
    contact = request.args.get('contact')
    if not contact:
        return jsonify({'error': 'Contact is required'}), 400

    # Query the database for a matching customer
    customer = next((c for c in customers if c['phone'] == contact), None)
    if not customer:
        return jsonify({'error': 'No customer found'}), 404

    return jsonify(customer), 200


if __name__ == '__main__':
    app.run(debug=True)
