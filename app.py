from flask import Flask, render_template, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://admin:12345@volunteerai.zt4yxsv.mongodb.net/?retryWrites=true&w=majority")

# Check connection
try:
    client.server_info()
    print("✅ MongoDB Connected Successfully")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)

db = client["volunteer_db"]
users = db["users"]

@app.route('/')
def home():
    return render_template("login.html")

# ✅ LOGIN
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = users.find_one({"email": email, "password": password})

    if user:
        return redirect('/dashboard')   # ✅ redirect added
    else:
        return "Invalid Email or Password ❌"

# ✅ SIGNUP
@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    company = request.form['company']
    email = request.form['email']
    password = request.form['password']

    # 🔥 CHECK IF USER EXISTS
    existing_user = users.find_one({"email": email})

    if existing_user:
        return "User already exists ❌"

    # INSERT NEW USER
    users.insert_one({
        "name": name,
        "company": company,
        "email": email,
        "password": password
    })

    return redirect('/')  # go back to login

# ✅ DASHBOARD
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
@app.route('/predict', methods=['POST'])
def predict():
    event_name = request.form['event_name']
    registered = int(request.form['registered'])

    # 🔥 SIMPLE PREDICTION LOGIC (for now)
    predicted = int(registered * 0.7)

    return render_template("dashboard.html", prediction=predicted)