import os
import random
import string
import uuid
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, send_file
from pymongo import MongoClient
import certifi
from flask_mail import Mail, Message
from datetime import datetime, timezone
from bson import ObjectId  # Import ObjectId to handle MongoDB ObjectId serialization
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from flask import request, jsonify, session
import bcrypt

# ====== CONFIGURATIONS ======
app = Flask(__name__, static_folder='static', template_folder='templates')

app.secret_key = os.urandom(24)

# MongoDB connection
client = MongoClient("mongodb+srv://agrinex_db_bhairava:Agrinex@cluster0.d4oijiu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["agrinex"]
admin_collection = db["admin"]

farmers_collection = db["farmers"]  # Connect to the farmers collection
buyers_collection = db["buyers"] 
# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'   # ⚡ Change this
app.config['MAIL_PASSWORD'] = 'your_app_password'       # ⚡ Change this
mail = Mail(app)

# OpenWeatherMap API Key
API_KEY = "b9641da9bd78b7aa49bcd685444e87f4"  # Replace with your API Key

# Load cleaned CSV file
df = pd.read_csv("cleaned_sorted_commodity_data.csv")

# Folder where models are saved
output_folder = "commodity_forecasts"

# ====== HELPER FUNCTIONS ======
def generate_code(length=6):
    digits = string.digits
    return 'AGR' + ''.join(random.choices(digits, k=length))

def correct_name(name):
    """
    Correct city or district name based on common English variants.
    """
    name = name.lower().strip()
    CITY_CORRECTIONS = {
        "bengaluru": "bangalore",
        "bengaluru urban": "bangalore urban",
        "bengaluru south": "bangalore south",
        "mysuru": "mysore",
        "mumbai suburban": "mumbai",
        "delhi": "new delhi",
    }
    return CITY_CORRECTIONS.get(name, name)

def get_weather(location):
    """
    Get current weather data using OpenWeatherMap Current Weather API.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={API_KEY}"
    response = requests.get(url)

    # Debugging: print the response to see the error message
    print(f"Response Code: {response.status_code}")
    print(f"Response Content: {response.text}")

    if response.status_code == 200:
        data = response.json()
        current = {
            "temperature": data['main']['temp'],
            "wind_speed": data['wind']['speed'],
            "precipitation": data.get('rain', {}).get('1h', 0.0)  # Rain in last 1 hour
        }
        return current
    else:
        return None

def get_forecast(location):
    """
    Get 5-day weather forecast using OpenWeatherMap 5-day/3-hour Forecast API and calculate daily averages.
    """
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&units=metric&appid={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        
        # Initialize a dictionary to store daily averages
        daily_data = {}

        for entry in data['list']:
            date = datetime.utcfromtimestamp(entry['dt']).strftime('%Y-%m-%d')
            if date not in daily_data:
                daily_data[date] = {
                    "temperature_sum": 0,
                    "wind_speed_sum": 0,
                    "precipitation_sum": 0,
                    "count": 0
                }
            
            # Sum up the values for each day
            daily_data[date]["temperature_sum"] += entry['main']['temp']
            daily_data[date]["wind_speed_sum"] += entry['wind']['speed']
            daily_data[date]["precipitation_sum"] += entry.get('rain', {}).get('3h', 0.0)
            daily_data[date]["count"] += 1
        
        # Calculate average values for each day
        daily_averages = {}
        for date, values in daily_data.items():
            daily_averages[date] = {
                "avg_temperature": values["temperature_sum"] / values["count"],
                "avg_wind_speed": values["wind_speed_sum"] / values["count"],
                "avg_precipitation": values["precipitation_sum"] / values["count"]
            }

        return daily_averages
    else:
        return None
    
def load_model(commodity_name):
    model_filename = f"{commodity_name.replace('/', '_')}_prophet_model.pkl"
    model_path = os.path.join(output_folder, model_filename)
    if os.path.exists(model_path):
        return joblib.load(model_path)
    else:
        return None
    # ---- New Function for Commodities ----
def get_available_commodities():
    """
    Function to return a list of available commodities.
    """
    available_commodities = df['Commodity'].unique().tolist()  # Get unique commodities from the cleaned CSV
    return available_commodities

# ====== LOGIN FUNCTION ======
def set_session_for_user(user_data, role):
    """
    Function to create session based on user type (farmer or buyer).
    """
    session['role'] = role  # Set role to farmer or buyer
    session['name'] = user_data.get("name", "")
    session['district'] = user_data.get("district", "")
    session['sub_district'] = user_data.get("sub_district", "")
    session['village'] = user_data.get("village", "")
    
    # Correctly assign the ID based on the role
    if role == 'farmer':
        session['id'] = str(user_data.get("farmer_id"))  # Use farmer_id for farmer
    elif role == 'buyer':
        session['id'] = str(user_data.get("buyer_id"))  # Use buyer_id for buyer

# ====== ROUTES ======

# Main Home Page
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    if 'role' in session:
        return render_template("home.html", session=session)
    else:
        return redirect("/")

# ---- Farmer Login
@app.route("/login/farmer", methods=["POST"])
def login_farmer():
    try:
        farmer_id = request.form.get("farmer_id")
        if not farmer_id:
            return jsonify({"status": "error", "message": "Farmer ID is required"}), 400

        farmer = db["farmers"].find_one({"farmer_id": farmer_id})  # Corrected collection name
        if farmer:
            set_session_for_user(farmer, 'farmer')  # Set session for farmer login
            return jsonify({
                "status": "success",
                "message": "Login successful!",
                "data": {
                    "name": farmer.get("name", "Farmer"),
                    "farmer_id": farmer.get("farmer_id"),
                    "location": farmer.get("location", "Unknown")
                }
            })
        else:
            return jsonify({"status": "error", "message": "Invalid Farmer ID"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---- Buyer Login
@app.route("/login/buyer", methods=["POST"])
def login_buyer():
    try:
        buyer_id = request.form.get("buyer_id")
        if not buyer_id:
            return jsonify({"status": "error", "message": "Buyer ID is required"}), 400

        buyer = db["buyers"].find_one({"buyer_id": buyer_id})
        if buyer:
            set_session_for_user(buyer, 'buyer')  # Set session for buyer login
            return jsonify({
                "status": "success",
                "message": "Login successful!",
                "name": buyer.get("username", "Buyer")
            })
        else:
            return jsonify({"status": "error", "message": "Invalid Buyer ID"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/weather", methods=["GET"])
def weather():
    if 'role' not in session:
        return "User not authenticated", 403

    role = session['role']
    if role == 'farmer':
        user_data = db["farmers"].find_one({"farmer_id": session['id']})
    elif role == 'buyer':
        user_data = db["buyers"].find_one({"buyer_id": session['id']})
    else:
        return "Invalid role", 403

    if user_data:
        state = user_data.get("state")
        district = user_data.get("district")
        sub_district = user_data.get("sub_district", "")
        village = user_data.get("village")
        
        # Format location as a string
        location = f"{village}, {sub_district}, {district}, {state}" if sub_district else f"{village}, {district}, {state}"

        # Fetch current weather data
        current_weather = get_weather(location)

        if current_weather:
            # Fetch 5-day forecast and calculate daily averages
            forecast = get_forecast(location)

            if forecast:
                return render_template("weather.html", current_weather=current_weather, forecast=forecast, location=location)
            else:
                return "❌ Failed to fetch the 5-day forecast.", 400
        else:
            return "❌ Failed to fetch current weather data.", 400
    else:
        return f"{role.capitalize()} data not found.", 404

@app.route("/commodities", methods=["GET"])
def get_commodities():
    available_commodities = get_available_commodities()
    return jsonify({"commodities": available_commodities})
    
@app.route("/predict", methods=["POST"])
def predict():
    commodity_name = request.json.get('commodity', '').strip()
    
    model = load_model(commodity_name)
    
    if model is None:
        return jsonify({"error": "Model not found for the commodity"}), 404

    # Start future dates from today
    today = datetime.now().date()

    future_dates = pd.date_range(start=today, periods=7, freq='D')
    future_df = pd.DataFrame({'ds': future_dates})

    # Predict future
    forecast = model.predict(future_df)

    # Extract dates and prices
    forecast_data = forecast[['ds', 'yhat']].to_dict(orient='records')

    # Add price per quintal at the end of each prediction
    for prediction in forecast_data:
        prediction['yhat_per_quintal'] = f"₹{prediction['yhat']:.2f} per quintal"
    
    return jsonify({"prediction": forecast_data})

@app.route("/graph", methods=["GET"])
def graph():
    commodity_name = request.args.get('commodity', '').strip()

    commodity_data = df[df['Commodity'] == commodity_name].copy()
    commodity_data['Arrival_Date'] = pd.to_datetime(commodity_data['Arrival_Date'], errors='coerce')
    commodity_data.dropna(subset=['Arrival_Date', 'Modal_Price'], inplace=True)
    commodity_data = commodity_data.sort_values(by='Arrival_Date')

    plt.figure(figsize=(10, 6))
    sns.lineplot(x='Arrival_Date', y='Modal_Price', data=commodity_data)
    plt.title(f"Price Trends for {commodity_name}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.xticks(rotation=45)

    # Save the plot to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')

@app.route("/inventory")
def inventory():
    if 'role' not in session or session['role'] != 'farmer':
        return redirect("/")  # Only farmers allowed, else redirect

    farmer_id = session['id']  # Get the farmer_id from session

    # Fetch all sales belonging to this farmer
    sales = list(db["sales"].find({"farmer_id": farmer_id}))

    return render_template('inventory.html', sales=sales)

@app.route("/weather-page")
def weather_page():
    return render_template("weather.html")

@app.route('/commodity_prediction')
def commodity_prediction():
    return render_template('commodity_prediction.html')

# ---- Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---- Admin Login
from werkzeug.security import check_password_hash
from flask import request, jsonify
# ---- Admin Login
from flask import Flask, redirect, url_for, request
@app.route('/login/admin', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        print(data)  # Log the incoming data
        admin_id = data.get('adminid')  # Use 'adminid' as the key here (user input)
        password = data.get('password')

        # Fetch the admin from the database by 'admin_id'
        admin = db["admin"].find_one({"admin_id": admin_id})
        print(f"Admin found: {admin}")  # Log the fetched admin to confirm it is in the database

        if admin:
            print(f"Stored password: {admin['password']}")  # Log the password from DB for comparison
            if admin['password'] == password:
                session['role'] = 'admin'
                session['adminid'] = admin_id
                return redirect(url_for('admin_dashboard'))
            else:
                return jsonify({"status": "error", "message": "Invalid admin credentials"}), 400
        else:
            return jsonify({"status": "error", "message": "Admin not found"}), 400
    except Exception as e:
        print(f"Error during admin login: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template(
        "admin_dashboard.html",
        admin_name="Ayush",
        farmer_count=15,  # replace with real value
        buyer_count=5     # replace with real value
    )
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

@app.route('/api/farmers', methods=['GET'])
def get_farmers():
    # Fetch all farmer records from the database
    farmers = farmers_collection.find()
    
    # Prepare data for response
    data = []
    for farmer in farmers:
        data.append({
            'id': str(farmer['_id']),  # Converting ObjectId to string for JSON response
            'farmer_id': farmer.get('farmer_id'),
            'name': farmer.get('name'),
            'phone': farmer.get('phone'),
            'district': farmer.get('district'),
            'sub_district': farmer.get('sub_district'),
            'village': farmer.get('village')
        })
    
    return jsonify({'data': data})

@app.route('/api/buyers', methods=['GET'])
def get_buyers():
    # Fetch all buyer records from the database
    buyers = buyers_collection.find()
    
    # Prepare data for response
    data = []
    for buyer in buyers:
        data.append({
            'id': str(buyer['_id']),  # Converting ObjectId to string for JSON response
            'buyer_id': buyer.get('buyer_id'),
            'username': buyer.get('username'),
            'email': buyer.get('email'),
            'phone': buyer.get('phone'),
            'district': buyer.get('district'),
            'sub_district': buyer.get('sub_district'),
            'village': buyer.get('village')
        })
    
    return jsonify({'data': data})
@app.route('/api/farmers/<farmer_id>', methods=['PUT'])
def update_farmer(farmer_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    result = farmers_collection.update_one(
        {'farmer_id': farmer_id},
        {'$set': {
            'name': data['name'],
            'phone': data['phone'],
            'district': data['district'],
            'sub_district': data['sub_district'],
            'village': data['village']
        }}
    )

    if result.matched_count:
        return jsonify({'message': 'Farmer updated successfully'}), 200
    return jsonify({'error': 'Farmer not found'}), 404

@app.route('/api/farmers/<farmer_id>', methods=['DELETE'])
def delete_farmer(farmer_id):
    result = farmers_collection.delete_one({'farmer_id': farmer_id})
    
    if result.deleted_count:
        return jsonify({'message': 'Farmer deleted successfully'}), 200
    else:
        return jsonify({'error': 'Farmer not found'}), 404

@app.route('/api/farmers', methods=['POST'])
def add_farmer():
    data = request.json
    farmer_id = str(uuid.uuid4())[:4]  # Or your own logic
    new_farmer = {
        'farmer_id': farmer_id,
        'name': data.get('name'),
        'phone': data.get('phone'),
        'district': data.get('district'),
        'sub_district': data.get('sub_district'),
        'village': data.get('village')
    }
    result = farmers_collection.insert_one(new_farmer)
    return jsonify({'message': 'Farmer added', 'id': str(result.inserted_id)})

@app.route('/api/buyers/<id>', methods=['PUT'])
def update_buyer(id):
    data = request.get_json()
    result = buyers_collection.update_one(
        {'_id': ObjectId(id)},
        {'$set': {
            'username': data['username'],
            'email': data['email'],
            'phone': data['phone'],
            'district': data['district'],
            'sub_district': data['sub_district'],
            'village': data['village']
        }}
    )

    if result.matched_count:
        return jsonify({'message': 'Buyer updated successfully'}), 200
    else:
        return jsonify({'error': 'Buyer not found'}), 404

@app.route('/api/buyers/<id>', methods=['DELETE'])
def delete_buyer(id):
    result = buyers_collection.delete_one({'_id': ObjectId(id)})
    
    if result.deleted_count:
        return jsonify({'message': 'Buyer deleted successfully'}), 200
    else:
        return jsonify({'error': 'Buyer not found'}), 404
@app.route('/admin/view-farmers')
def view_farmers():
    return render_template('view_farmers.html')

@app.route('/admin/view-buyers')
def view_buyers():
    return render_template('view_buyers.html')
@app.route('/admin/alerts')
def alerts():
    return render_template('alerts.html')

# Collection for emergency requests
emergency_collection = db['emergency_requests']

# API route to fetch emergency alerts
@app.route('/api/alerts/')
def get_emergency_alerts():
    emergencies = list(emergency_collection.find({}, {
        '_id': 0,  # Exclude _id
        'farmer_id': 1,
        'category': 1,
        'description': 1,
        'status': 1,
        'timestamp': 1
    }))
    return jsonify(emergencies)  # Return the emergencies data

# API route to update the status of an emergency request
@app.route('/api/emergency_requests/<request_id>', methods=['PUT'])
def update_emergency_status(request_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status required'}), 400

    result = emergency_collection.update_one(
        {'_id': request_id},  # Use '_id' to match the request_id
        {'$set': {'status': data['status']}}
    )
    if result.matched_count:
        return jsonify({'message': 'Status updated'}), 200
    return jsonify({'error': 'Request not found'}), 404
@app.route('/admin/sales')
def sales():
    return render_template('sales.html')
sales_collection = db['sales']

@app.route('/api/sales/')
def get_sales():
    sales = list(sales_collection.find({}, {
        '_id': 0,
        'farmer_id': 1,
        'name': 1,
        'phone': 1,
        'village': 1,
        'commodity': 1,
        'quantity_kg': 1,
        'price_per_kg': 1,
        'total_price': 1,
        'timestamp': 1
    }))
    return jsonify(sales)
@app.route('/admin/analytics')
def analytics():
    sales = list(db['sales'].find({}, {'_id': 0}))
    return render_template('analytics.html', sales=sales)

# ====== START SERVER ======
if __name__ == "__main__":
    app.run(debug=True)
