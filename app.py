from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DB =================
client = MongoClient("mongodb+srv://admin:12345@volunteerai.zt4yxsv.mongodb.net/?retryWrites=true&w=majority")
db = client["volunteer_db"]

users = db["users"]
events = db["events"]

MODEL_PATH = "model.pkl"

# ================= HELPER =================
def get_trained_events():
    return [e for e in events.find() if "actual_turnout" in e and "registered" in e]

# ================= FEATURE VECTOR =================
def build_feature_vector(data):
    return [
        int(data.get('registered', 0)),

        int(data.get('event_type', 0)),
        int(data.get('event_time', 0)),
        int(data.get('day_of_week', 1)),
        int(data.get('duration_hours', 1)),
        int(data.get('conflicting_events', 0)),

        float(data.get('confirmation_rate', 50)) / 100,
        float(data.get('last_minute_pct', 20)) / 100,
        float(data.get('past_attendance', 70)) / 100,

        int(data.get('weather', 0)),
        int(data.get('season', 0)),

        float(data.get('distance_km', 10)),
        int(data.get('transport_available', 1)),
        int(data.get('location_type', 0)),

        int(data.get('reminders_sent', 1)),
        float(data.get('response_rate', 50)) / 100,
        float(data.get('social_influence', 30)) / 100,

        int(data.get('org_reputation', 1)),
        int(data.get('perks', 0)),

        int(data.get('avg_age', 1)),
        int(data.get('motivation', 0)),
        int(data.get('safety_rating', 1))
    ]

# ================= TRAIN MODEL =================
def train_model():
    past = get_trained_events()

    if len(past) < 20:
        return None

    X, y = [], []

    for e in past:
        try:
            X.append(build_feature_vector(e))
            y.append(e['actual_turnout'])
        except:
            continue

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    return model

# ================= LOAD MODEL =================
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return train_model()

# ================= PREDICT =================
def predict_turnout(data):
    registered = int(data.get('registered', 0))
    model = load_model()

    features = build_feature_vector(data)

    if model:
        pred = int(model.predict([features])[0])
    else:
        pred = int(registered * 0.70)

    return min(max(pred, 0), registered)

# ================= ACCURACY =================
def calculate_accuracy():
    past = get_trained_events()

    if len(past) < 5:
        return None

    errors = []
    for e in past:
        actual = e.get('actual_turnout', 0)
        pred = e.get('predicted', 0)

        if actual > 0:
            errors.append(abs(pred - actual) / actual)

    if errors:
        return round((1 - np.mean(errors)) * 100, 2)
    return None

# ================= ROUTES =================
@app.route('/')
def home():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    user = users.find_one({
        "email": request.form['email'],
        "password": request.form['password']
    })

    if user:
        session['user_email'] = user['email']
        return redirect('/dashboard')

    return "Invalid Email or Password ❌"

@app.route('/signup', methods=['POST'])
def signup():
    if users.find_one({"email": request.form['email']}):
        return "User already exists ❌"

    users.insert_one({
        "name": request.form['name'],
        "company": request.form['company'],
        "email": request.form['email'],
        "password": request.form['password']
    })

    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect('/')

    user = users.find_one({"email": session['user_email']})
    all_events = list(events.find({"user_email": session['user_email']}))

    for e in all_events:
        e["_id"] = str(e["_id"])

    total_events = len(all_events)
    total_volunteers = sum(e.get('registered', 0) for e in all_events)
    total_predicted = sum(e.get('predicted', 0) for e in all_events)

    today = datetime.today().strftime('%Y-%m-%d')
    upcoming = sum(
        1 for e in all_events
        if e.get('event_date') and e['event_date'] >= today
    )

    accuracy = calculate_accuracy()

    return render_template(
        "dashboard.html",
        user=user,
        total_events=total_events,
        volunteers=total_volunteers,
        predicted=total_predicted,
        upcoming=upcoming,
        events=all_events,
        accuracy=accuracy
    )

@app.route('/predict', methods=['POST'])
def predict():
    if 'user_email' not in session:
        return redirect('/')

    try:
        data = request.form.to_dict()
        data['registered'] = int(request.form['registered'])

        predicted = predict_turnout(data)

        events.insert_one({
            **data,
            "predicted": predicted,
            "user_email": session['user_email']
        })

    except Exception as e:
        print("Prediction error:", e)

    return redirect('/dashboard')

@app.route('/actual/<event_id>', methods=['POST'])
def record_actual(event_id):
    if 'user_email' not in session:
        return redirect('/')

    try:
        from bson import ObjectId

        actual = int(request.form['actual_turnout'])

        event = events.find_one({"_id": ObjectId(event_id)})
        predicted = event.get('predicted', 0)

        events.update_one(
            {"_id": ObjectId(event_id)},
            {
                "$set": {
                    "actual_turnout": actual,
                    "error": abs(actual - predicted)
                }
            }
        )

        # 🔥 retrain model after new data
        train_model()

    except Exception as e:
        print("Actual update error:", e)

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)