from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

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

# AI MODEL
def predict_turnout(registered):
    past_events = list(events.find())

    if len(past_events) < 2:
        return int(registered * 0.7)

    X = []
    y = []

    for e in past_events:
        if "registered" in e and "predicted" in e:
            X.append([e["registered"]])
            y.append(e["predicted"])

    model = LinearRegression()
    model.fit(X, y)

    return int(model.predict([[registered]])[0])

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect('/')

    user = users.find_one({"email": session['user_email']})
    all_events = list(events.find({"user_email": session['user_email']}))

    for event in all_events:
        event["_id"] = str(event["_id"])

    total_events = len(all_events)
    total_volunteers = sum(e.get('registered', 0) for e in all_events)
    total_predicted = sum(e.get('predicted', 0) for e in all_events)

    today = datetime.today().strftime('%Y-%m-%d')
    upcoming = sum(
        1 for e in all_events
        if e.get('event_date') and e['event_date'] >= today
    )

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
@app.route('/predict', methods=['POST'])
def predict():
    if 'user_email' not in session:
        return redirect('/')

    event_name = request.form['event_name']
    event_date = request.form['event_date']
    registered = int(request.form['registered'])

    predicted = predict_turnout(registered)

    events.insert_one({
        "event_name": event_name,
        "event_date": event_date,
        "registered": registered,
        "predicted": predicted,
        "user_email": session['user_email']
    })

    return redirect('/dashboard')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# RUN
if __name__ == "__main__":
    app.run(debug=True)