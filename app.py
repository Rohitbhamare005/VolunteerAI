from flask import Flask, render_template, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://admin:12345@volunteerai.zt4yxsv.mongodb.net/?retryWrites=true&w=majority")

db = client["volunteer_db"]
users = db["users"]
events = db["events"]

# HOME
@app.route('/')
def home():
    return render_template("login.html")

# LOGIN
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = users.find_one({"email": email, "password": password})

    if user:
        return redirect('/dashboard')
    else:
        return "Invalid Email or Password ❌"

# SIGNUP
@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    company = request.form['company']
    email = request.form['email']
    password = request.form['password']

    if users.find_one({"email": email}):
        return "User already exists ❌"

    users.insert_one({
        "name": name,
        "company": company,
        "email": email,
        "password": password
    })

    return redirect('/')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    all_events = list(events.find())

    total_events = len(all_events)
    total_volunteers = sum(e.get('registered', 0) for e in all_events)
    total_predicted = sum(e.get('predicted', 0) for e in all_events)
    upcoming = len(all_events)

    return render_template(
        "dashboard.html",
        total_events=total_events,
        volunteers=total_volunteers,
        predicted=total_predicted,
        upcoming=upcoming,
        events=all_events
    )

# PREDICT + STORE
@app.route('/predict', methods=['POST'])
def predict():
    try:
        event_name = request.form['event_name']
        registered = int(request.form['registered'])

        # simple prediction logic
        predicted = int(registered * 0.7)

        events.insert_one({
            "event_name": event_name,
            "registered": registered,
            "predicted": predicted
        })

    except Exception as e:
        print("Error:", e)

    return redirect('/dashboard')

# RUN APP
if __name__ == "__main__":
    app.run(debug=True)