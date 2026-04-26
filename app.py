from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import numpy as np
from sklearn.linear_model import LinearRegression
app = Flask(__name__)
app.secret_key = "secret123"

# MongoDB
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
        session['user_email'] = email
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
    if 'user_email' not in session:
        return redirect('/')

    user = users.find_one({"email": session['user_email']})

    all_events = list(events.find({"user_email": session['user_email']}))

    # 🔥 FIX: Convert ObjectId → string
    for event in all_events:
        event["_id"] = str(event["_id"])

    total_events = len(all_events)
    total_volunteers = sum(e.get('registered', 0) for e in all_events)
    total_predicted = sum(e.get('predicted', 0) for e in all_events)
    upcoming = len(all_events)

    return render_template(
        "dashboard.html",
        user=user,
        total_events=total_events,
        volunteers=total_volunteers,
        predicted=total_predicted,
        upcoming=upcoming,
        events=all_events
    )
# PREDICT
def predict_turnout(registered):
    past_events = list(events.find())

    # Need at least 2 data points
    if len(past_events) < 2:
        return int(registered * 0.7)

    X = []
    y = []

    for e in past_events:
        if "registered" in e and "predicted" in e:
            X.append([e["registered"]])
            y.append(e["predicted"])

    X = np.array(X)
    y = np.array(y)

    model = LinearRegression()
    model.fit(X, y)

    prediction = model.predict([[registered]])

    return int(prediction[0])
@app.route('/predict', methods=['POST'])
def predict():
    if 'user_email' not in session:
        return redirect('/')

    try:
        event_name = request.form['event_name']
        registered = int(request.form['registered'])

        # 🔥 AI prediction
        predicted = predict_turnout(registered)

        events.insert_one({
            "event_name": event_name,
            "registered": registered,
            "predicted": predicted,
            "user_email": session['user_email']
        })

    except Exception as e:
        print("Error:", e)

    return redirect('/dashboard')
# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# RUN
if __name__ == "__main__":
    app.run(debug=True)