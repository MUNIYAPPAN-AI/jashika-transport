from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
import certifi
from datetime import datetime
import os  # Deployment-ku mukkiyam

app = Flask(__name__)
# Secret key session maintain panna mukkiyam
app.secret_key = "jashika_transport_key_123"

# --- MongoDB Atlas Connection ---
uri = "mongodb+srv://rural_admin:munik123@cluster0.gmmemqo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Global variables
client = None
db = None
loads_col = None

try:
    client = MongoClient(uri, tlsCAFile=certifi.where())
    db = client['jashika_transport']
    loads_col = db['loads'] 
    client.admin.command('ping')
    print("MongoDB Connected Successfully!")
except Exception as e:
    print(f"Connection Error: {e}")

# --- 0. Login & Session Logic ---
@app.route('/')
def home():
    # User munnadiye login panni irundha direct-ah dashboard-ku poga vakkrom
    if 'user' in session:
        return redirect(url_for('bill_entry'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == 'pandi':
        session['user'] = 'pandi'  # Session start panrom
        return redirect(url_for('bill_entry'))
    else:
        flash("Wrong Password!")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None) # Session-ah clear panrom
    return redirect(url_for('home'))

# --- 1. Dashboard (index.html) ---
@app.route('/bill_entry')
def bill_entry():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('index.html')

# --- 2. Create New Bill Page ---
@app.route('/create_bill')
def create_bill():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('create_bill.html')

# --- 3. Save Manual Bill Data ---
@app.route('/save_bill', methods=['POST'])
def save_bill():
    if 'user' not in session:
        return redirect(url_for('home'))
        
    global loads_col
    if loads_col is None:
        return "Database Connection missing!"

    bill_data = {
        "invoice_no": request.form.get('inv_no'),
        "date": request.form.get('date'),
        "dispatch": request.form.get('dispatch'),
        "destination": request.form.get('destination'),
        "party_name": request.form.get('party_name'),
        "particulars": request.form.get('particulars'),
        "qty": request.form.get('qty'),
        "amount": request.form.get('amount'),
        "type": "bill"
    }

    try:
        loads_col.insert_one(bill_data)
        flash("Manual Bill Saved to Database!")
        return redirect(url_for('view_bills'))
    except Exception as e:
        return f"Error saving bill: {e}"

# --- 4. View All Bills Page ---
@app.route('/view_bills')
def view_bills():
    if 'user' not in session:
        return redirect(url_for('home'))
        
    global loads_col
    try:
        all_loads = list(loads_col.find())
        return render_template('view_bills.html', loads=all_loads)
    except Exception as e:
        return f"Template Error: {e}"

# --- 5. Permanent Load Save via JSON (AJAX) ---
@app.route('/save_load_permenant', methods=['POST'])
def save_load_permenant():
    if 'user' not in session:
        return jsonify({"message": "Unauthorized"}), 401
        
    global loads_col
    data = request.json
    if loads_col is None:
        return jsonify({"message": "Database error"}), 500

    load_entry = {
        "destination": data.get('state'),
        "amount": data.get('amount'),
        "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "type": "load_entry"
    }

    try:
        loads_col.insert_one(load_entry)
        return jsonify({"message": "Load saved permenantly with date!"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# --- 6. Fetch Loads for Live Table ---
@app.route('/get_loads', methods=['GET'])
def get_loads():
    global loads_col
    try:
        # Load entry data-va mattum list panrom
        loads = list(loads_col.find({"type": "load_entry"}, {"_id": 0}).sort("_id", -1).limit(10))
        return jsonify(loads)
    except Exception as e:
        return jsonify([])

# --- 7. Reset Stats (Clearing Load Entries) ---
@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    if 'user' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    global loads_col
    try:
        if loads_col is not None:
            # Type 'load_entry' irukura ella data-vaiyum permanent-ah delete panrom
            loads_col.delete_many({"type": "load_entry"}) 
            return jsonify({"status": "success", "message": "All load records cleared!"})
        return jsonify({"status": "error", "message": "Database not connected"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 8. Add Load (Traditional Form) ---
@app.route('/add_load', methods=['POST'])
def add_load():
    if 'user' not in session:
        return redirect(url_for('home'))
        
    global loads_col
    state = request.form.get('state')
    amount = request.form.get('amount')

    if loads_col is None:
        return "Database Connection missing!"

    if state and amount:
        try:
            loads_col.insert_one({
                "destination": state, 
                "amount": amount,
                "date": datetime.now().strftime("%d-%m-%Y"),
                "type": "load_entry"
            })
            flash("Data Successfully Saved to Cloud!")
            return redirect(url_for('view_bills'))
        except Exception as e:
            return f"Database Error: {e}"
    
    flash("Please fill all fields!")
    return redirect(url_for('bill_entry'))

# --- Final Step for Deployment ---
if __name__ == '__main__':
    # Local-layum vela seiyum, Render-oda dynamic port-layum vela seiyum
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)