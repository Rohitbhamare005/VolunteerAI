from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)

# 🔐 Secret key for session
app.secret_key = "secret123"

# 🌐 MongoDB connection
client = MongoClient("mongodb+srv://admin:12345@volunteerai.zt4yxsv.mongodb.net/?retryWrites=true&w=majority")

# Check connection
try:
    client.server_info()
    print("✅ MongoDB Connected Successfully")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)

db = client["volunteer_db"]
users = db["users"]

# 🏠 HOME (LOGIN PAGE)
@app.route('/')
def home():
    return render_template("login.html")

# 🔑 LOGIN
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = users.find_one({"email": email})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        session['user'] = email
        return redirect('/dashboard')
    else:
        return "Invalid Email or Password ❌"

# 📝 SIGNUP
@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    company = request.form['company']
    email = request.form['email']
    password = request.form['password']

    # Check if user exists
    existing_user = users.find_one({"email": email})

    if existing_user:
        return "User already exists ❌"

    # 🔐 Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert user
    users.insert_one({
        "name": name,
        "company": company,
        "email": email,
        "password": hashed_password
    })

    return redirect('/')

# 📊 DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    return render_template("dashboard.html")

# 🤖 PREDICTION
@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect('/')

    event_name = request.form['event_name']
    registered = int(request.form['registered'])

    # 🔥 Improved logic
    if registered < 50:
        predicted = int(registered * 0.6)
    elif registered < 200:
        predicted = int(registered * 0.7)
    else:
        predicted = int(registered * 0.8)

    return render_template("dashboard.html", prediction=predicted, event=event_name)

# 🚪 LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# ▶️ RUN APP
if __name__ == "__main__":
    app.run(debug=True)