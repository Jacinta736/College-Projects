from flask import Flask, request, jsonify, render_template, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "secretkey"

# ─────────────────────────────────────────────
# DB — reconnects automatically if connection drops
# ─────────────────────────────────────────────

DB_CONFIG = dict(
    host="localhost",
    user="root",
    password="7152",
    database="financial_systems"
)

_db = None

def get_db():
    global _db
    try:
        if _db is None or not _db.is_connected():
            _db = mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error:
        _db = mysql.connector.connect(**DB_CONFIG)
    return _db

def query(sql, params=(), one=False):
    """Run a SELECT and return one row or all rows."""
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(sql, params)
    return cur.fetchone() if one else cur.fetchall()

def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE, commit, and return lastrowid."""
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(sql, params)
    db.commit()
    return cur.lastrowid


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password), one=True
        )
        if user:
            session['userid'] = user['userid']
            session['role']   = user['role']
            return redirect('/customer' if user['role'] == 'Customer' else '/admin')
        return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ─────────────────────────────────────────────
# CUSTOMER – pages
# ─────────────────────────────────────────────

@app.route('/customer')
def customer_dashboard():
    if session.get('role') != 'Customer':
        return redirect('/')
    return render_template('customer.html')


# ─────────────────────────────────────────────
# CUSTOMER – API endpoints
# ─────────────────────────────────────────────

@app.route('/personal_details')
def personal_details():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query("SELECT * FROM personal_details WHERE userid=%s", (session['userid'],), one=True)
    return jsonify(data)


@app.route('/account_details')
def account_details():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query("""
        SELECT a.accountid, a.accounttype, a.balance, a.currency, a.createdate
        FROM accounts a
        JOIN customers c ON a.customerid = c.customerid
        WHERE c.userid = %s
    """, (session['userid'],))
    return jsonify(data)


@app.route('/my_transactions')
def my_transactions():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query("""
        SELECT * FROM transaction_details
        WHERE from_userid = %s OR to_userid = %s
        ORDER BY transactiondate DESC
    """, (session['userid'], session['userid']))
    return jsonify(data)


@app.route('/open_account', methods=['POST'])
def open_account():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    accounttype = request.form['accounttype']
    currency    = request.form.get('currency', 'INR')
    try:
        customer = query(
            "SELECT customerid FROM customers WHERE userid = %s",
            (session['userid'],), one=True
        )
        if not customer:
            return jsonify({'success': False, 'message': 'Customer record not found'})
        accountid = execute(
            "INSERT INTO accounts (customerid, accounttype, currency) VALUES (%s, %s, %s)",
            (customer['customerid'], accounttype, currency)
        )
        return jsonify({'success': True, 'message': f'Account #{accountid} created successfully!', 'accountid': accountid})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/deposit', methods=['POST'])
def deposit():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        execute(
            "INSERT INTO transactions (toaccount, transactiontype, amount) VALUES (%s, 'Deposit', %s)",
            (request.form['account'], request.form['amount'])
        )
        return jsonify({'success': True, 'message': 'Deposit successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/withdraw', methods=['POST'])
def withdraw():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        execute(
            "INSERT INTO transactions (fromaccount, transactiontype, amount) VALUES (%s, 'Withdraw', %s)",
            (request.form['account'], request.form['amount'])
        )
        return jsonify({'success': True, 'message': 'Withdrawal successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/transfer', methods=['POST'])
def transfer():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        execute(
            "INSERT INTO transactions (fromaccount, toaccount, transactiontype, amount) VALUES (%s, %s, 'Transfer', %s)",
            (request.form['from'], request.form['to'], request.form['amount'])
        )
        return jsonify({'success': True, 'message': 'Transfer successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/cards')
def view_cards():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query("""
        SELECT cd.cardid, cd.accountno, cd.cardtype, cd.cardnumber, cd.Expiry
        FROM card_details cd
        WHERE cd.userid = %s
    """, (session['userid'],))
    return jsonify(data)


@app.route('/add_card', methods=['POST'])
def add_card():
    if session.get('role') != 'Customer':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        execute(
            "INSERT INTO cards (accountno, cardtype, cardnumber, Expiry, cvv) VALUES (%s, %s, %s, %s, %s)",
            (request.form['account'], request.form['type'], request.form['number'],
            request.form['expiry'], request.form['cvv'])
        )
        return jsonify({'success': True, 'message': 'Card added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ─────────────────────────────────────────────
# ADMIN – pages
# ─────────────────────────────────────────────

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'Admin':
        return redirect('/')
    return render_template('admin.html')


# ─────────────────────────────────────────────
# ADMIN – API endpoints
# ─────────────────────────────────────────────

@app.route('/all_customers')
def all_customers():
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query("""
        SELECT c.customerid, c.firstname, c.lastname, c.email, c.phone,
        c.dob, c.Address, c.DOCreation, u.username
        FROM customers c
        JOIN users u ON c.userid = u.userid
    """)
    return jsonify(data)


@app.route('/transactions_log')
def transactions_log():
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query("SELECT * FROM transactions ORDER BY transactiondate DESC")
    return jsonify(data)


@app.route('/admin/customer_accounts')
def admin_customer_accounts():
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query(
        "SELECT accountid, accounttype, balance, currency, createdate FROM accounts WHERE customerid = %s",
        (request.args.get('customerid'),)
    )
    return jsonify(data)


@app.route('/admin/customer_transactions')
def admin_customer_transactions():
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = query("""
        SELECT DISTINCT t.transactionid, t.fromaccount, t.toaccount,
        t.transactiontype, t.amount, t.transactiondate
        FROM transactions t
        LEFT JOIN accounts fa ON t.fromaccount = fa.accountid
        LEFT JOIN accounts ta ON t.toaccount   = ta.accountid
        WHERE fa.customerid = %s OR ta.customerid = %s
        ORDER BY t.transactiondate DESC
    """, (request.args.get('customerid'), request.args.get('customerid')))
    return jsonify(data)


@app.route('/add_customer', methods=['POST'])
def add_customer():
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    username = request.form['username']
    password = request.form['password']
    fname    = request.form['fname']
    lname    = request.form.get('lname', '')
    email    = request.form.get('email', '')
    phone    = request.form.get('phone', '')
    try:
        userid = execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, 'Customer')",
            (username, password)
        )
        execute(
            "INSERT INTO customers (userid, firstname, lastname, email, phone, DOCreation) VALUES (%s, %s, %s, %s, %s, CURDATE())",
            (userid, fname, lname, email, phone)
        )
        return jsonify({'success': True, 'message': f"Customer '{username}' added successfully"})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True)