from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
import certifi
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "jashika_transport_key_123"

# --- MongoDB Atlas Connection ---
uri = "mongodb+srv://rural_admin:munik123@cluster0.gmmemqo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

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

# --- Routes ---

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('bill_entry'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == 'pandi':
        session['user'] = 'pandi'
        return redirect(url_for('bill_entry'))
    else:
        flash("Wrong Password!")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/bill_entry')
def bill_entry():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/create_bill')
def create_bill():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('create_bill.html')

# --- PUDHU QUOTATION ROUTE (Ippo Add Panniyathu) ---
@app.route('/quotation')
def quotation():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('quotation.html')

@app.route('/save_bill', methods=['POST'])
def save_bill():
    if 'user' not in session:
        return redirect(url_for('home'))
        
    global loads_col
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
        # Voice alert-kaga 'voice' nu category kudukrom
        flash("Manual Bill Saved Successfully", "voice")
        return redirect(url_for('view_bills'))
    except Exception as e:
        return f"Error saving bill: {e}"

@app.route('/view_bills')
def view_bills():
    if 'user' not in session:
        return redirect(url_for('home'))
    global loads_col
    try:
        all_loads = list(loads_col.find())
        return render_template('view_bills.html', loads=all_loads)
    except Exception as e:
        return f"Database Error: {e}"

@app.route('/save_load_permenant', methods=['POST'])
def save_load_permenant():
    if 'user' not in session: return jsonify({"message": "Unauthorized"}), 401
    global loads_col
    data = request.json
    load_entry = {
        "destination": data.get('state'),
        "amount": data.get('amount'),
        "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "type": "load_entry"
    }
    try:
        loads_col.insert_one(load_entry)
        return jsonify({"message": "Load saved permenantly!"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/get_loads', methods=['GET'])
def get_loads():
    global loads_col
    try:
        loads = list(loads_col.find({"type": "load_entry"}, {"_id": 0}).sort("_id", -1).limit(10))
        return jsonify(loads)
    except Exception as e:
        return jsonify([])

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    if 'user' not in session: return jsonify({"status": "error"}), 401
    global loads_col
    try:
        loads_col.delete_many({"type": "load_entry"}) 
        return jsonify({"status": "success", "message": "Records cleared!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/add_load', methods=['POST'])
def add_load():
    if 'user' not in session:
        return redirect(url_for('home'))
    global loads_col
    state = request.form.get('state')
    amount = request.form.get('amount')

    if state and amount:
        try:
            loads_col.insert_one({
                "destination": state, 
                "amount": amount,
                "date": datetime.now().strftime("%d-%m-%Y"),
                "type": "load_entry"
            })
            # Voice alert category
            flash("Data Successfully Saved to Cloud", "voice")
            return redirect(url_for('view_bills'))
        except Exception as e:
            return f"Database Error: {e}"
    
    flash("Please fill all fields!")
    return redirect(url_for('bill_entry'))

# --- Final Step (Pop-up Fix) ---
if __name__ == '__main__':
    # Local-la run panna host '127.0.0.1' use panrom. 
    app.run(host='127.0.0.1', port=5000, debug=True)