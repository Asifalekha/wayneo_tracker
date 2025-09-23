# from flask import Flask, request, render_template, jsonify
# import json
# from flask_cors import CORS
# import requests
# import math
# import threading
# import time
#
# app = Flask(__name__)
# CORS(app)
#
# #dataset for bus
# buses= [
#     {
#         "bus_number": "19B",
#         "start_stop": "Kelambakkam",
#         "end_stop": "Broadway",
#         "stops": [
#             "Kelambakkam",
#             "Siruseri IT Park",
#             "Sholinganallur",
#             "Tidel Park",
#             "Rajiv Gandhi Salai",
#             "Saidapet",
#             "Anna University",
#             "Guindy",
#             "Broadway"
#         ]
#     },
#     {
#         "bus_number": "23C",
#         "start_stop": "Thiruvanmiyur",
#         "end_stop": "Anna University",
#         "stops": [
#             "Thiruvanmiyur",
#             "Tidel Park",
#             "Rajiv Gandhi Salai",
#             "Saidapet",
#             "Anna University"
#         ]
#     },
#     {
#         "bus_number": "570",
#         "start_stop": "Kelambakkam",
#         "end_stop": "CMBT",
#         "stops": [
#             "Kelambakkam",
#             "Sholinganallur",
#             "Tidel Park",
#             "Rajiv Gandhi Salai",
#             "Saidapet",
#             "Anna University",
#             "Koyambedu CMBT"
#         ]
#     }
# ]
#
#
# # In-memory store for live user locations
# live_locations = {}  # list of {"latitude": ..., "longitude": ...}
# # In-memory store for buses
# live_buses = {}  # {"bus_number": {"lat": ..., "lng": ..., "route_coords": [...], "idx": 0}}
#
#
# # live_locations.append({"latitude": 13.0100, "longitude": 80.2100})
# # live_locations.append({"latitude": 13.0120, "longitude": 80.2120})
# # live_locations.append({"latitude": 13.0150, "longitude": 80.2150})
#
# def normalize(text):
#     return text.lower().replace(" ", "")
# def move_buses():
#     while True:
#         for bus_number, bus in live_buses.items():
#             # Move along the route
#             if bus["idx"] < len(bus["route_coords"]) - 1:
#                 bus["idx"] += 1
#                 bus["lat"], bus["lng"] = bus["route_coords"][bus["idx"]]
#             else:
#                 # Optionally loop or reset
#                 bus["idx"] = 0
#         time.sleep(2)  # Update every 2 seconds
#
# @app.route('/set_route', methods=['POST'])
# def set_route():
#     data = request.get_json()
#     source = data.get("source")
#     destination = data.get("destination")
#     print("User chose:", source, "->", destination)
#     # Save to session/global/db as needed
#     return jsonify({"status": "ok", "source": source, "destination": destination})
#
#
# def stop_matches(user_stop, stop_list):
#     user_norm = normalize(user_stop)
#     for s in stop_list:
#         if user_norm in normalize(s) or normalize(s) in user_norm:
#             return True
#     return False
#
#
# def initialize_buses_on_route(start_location, end_location):
#     buses_on_route = find_bus(start_location, end_location)
#     for bus in buses_on_route:
#         # Get route coordinates for this bus
#         start_lat, start_lng = geocode(start_location)
#         end_lat, end_lng = geocode(end_location)
#         route_coords = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng)
#
#         live_buses[bus["bus_number"]] = {
#             "route_coords": route_coords,
#             "idx": 0,
#             "lat": route_coords[0][0],
#             "lng": route_coords[0][1]
#         }
#
#
# # --- Geocoding function: location name -> coordinates ---
#
#
# def geocode(location_name):
#     """
#     Geocode a location in Chennai using Nominatim with bounding box and single q parameter.
#     Returns (latitude, longitude) or (None, None) if not found.
#     """
#
#     # Chennai bounding box: left, bottom, right, top
#     viewbox = "80.17,12.95,80.35,13.15"
#
#     url = "https://nominatim.openstreetmap.org/search"
#     params = {
#         "q": f"{location_name}, Chennai, Tamil Nadu, India",  # single q string
#         "format": "json",
#         "limit": 1,
#         "bounded": 1,
#         "viewbox": viewbox
#     }
#     headers = {"User-Agent": "WayneoApp/1.0 (asifalekha@gmail.com)"}  # REQUIRED
#
#     res = requests.get(url, params=params, headers=headers)
#     res.raise_for_status()
#     data = res.json()
#
#     if not data:
#         return None, None
#
#     # Extract coordinates
#     lat = float(data[0]["lat"])
#     lng = float(data[0]["lon"])
#
#     # Optional: confirm the returned city is Chennai
#     address = data[0].get("display_name", "")
#     if "Chennai" not in address:
#         return None, None
#
#     return lat, lng
#
#
#
#
# # --- Get route from OSRM ---
# def get_route_from_osrm(start_lat, start_lng, end_lat, end_lng):
#     url = f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
#     res = requests.get(url)
#     res.raise_for_status()
#     data = res.json()
#     coords = data["routes"][0]["geometry"]["coordinates"]
#     # Convert lng, lat → lat, lng
#     return [(lat, lng) for lng, lat in coords]
#
#
# # --- Haversine distance ---
# def haversine(lat1, lng1, lat2, lng2):
#     R = 6371  # km
#     phi1 = math.radians(lat1)
#     phi2 = math.radians(lat2)
#     dphi = math.radians(lat2 - lat1)
#     dlambda = math.radians(lng2 - lng1)
#     a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     return R * c  # distance in km
#
#
# #finding the bus in the certain route
# def find_bus(start_location, end_location):
#     available = []
#     for bus in buses:
#         stops = bus["stops"]
#
#         if stop_matches(start_location, stops) and stop_matches(end_location, stops):
#             start_idx = [i for i, s in enumerate(stops) if stop_matches(start_location, [s])][0]
#             end_idx = [i for i, s in enumerate(stops) if stop_matches(end_location, [s])][0]
#
#             if start_idx < end_idx:  # ensure direction is valid
#                 # Estimate ETA: assume 5 min per stop + crowd delay
#                 eta = (end_idx - start_idx) * 5
#                 available.append({
#                     "bus_number": bus["bus_number"],
#                     "start_stop": bus["start_stop"],
#                     "end_stop": bus["end_stop"],
#                     "eta_min": eta
#                 })
#     return available
#
#
#
# # --- Match crowd along route ---
# # def match_crowd_data(route_coords):
# #     matched_points = []
# #     for lat, lng in route_coords:
# #         # count number of live users within 0.05 km (~50 meters)
# #         people = sum(
# #             1 for loc in live_locations if haversine(lat, lng, loc["latitude"], loc["longitude"]) < 1.8
# #         )
# #         dots = math.ceil(people / 1)  # 1 dot per person
# #         matched_points.append({
# #             "latitude": float(lat),
# #             "longitude": float(lng),
# #             "people_count": people,
# #             "dots": int(dots)
# #         })
# #     return matched_points
# #
#
#
# ##new crowd
# # def match_crowd_data(route_coords, threshold_km=0.8):
# #     matched_points = []
# #     for lat, lng in route_coords:
# #         # Only count users within `threshold_km` of this route point
# #         people = sum(
# #             1 for loc in live_locations
# #             if haversine(lat, lng, loc["latitude"], loc["longitude"]) <= threshold_km
# #         )
# #         if people > 0:  # Only add points where someone is actually present
# #             matched_points.append({
# #                 "latitude": float(lat),
# #                 "longitude": float(lng),
# #                 "people_count": people,
# #                 "dots": people
# #             })
# #     return matched_points
#
# ##now changed
# def match_crowd_data(route_coords, threshold_km=0.5):
#     crowd_points = []
#     for lat, lng in route_coords:
#         people = sum(
#             1 for loc in live_locations.values()
#             if haversine(lat, lng, loc["latitude"], loc["longitude"]) <= threshold_km
#         )
#         if people > 0:
#             crowd_points.append({"latitude": lat, "longitude": lng, "count": people})
#     return crowd_points
#
#
# # --- Home page: enter start/end locations ---
# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         start_location = request.form["start_location"]
#         end_location = request.form["end_location"]
#
#         start_lat, start_lng = geocode(start_location)
#         end_lat, end_lng = geocode(end_location)
#
#         if start_lat is None or end_lat is None:
#             return "Could not find one of the locations. Please try again."
#
#         route_coords = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng)
#         crowd_points = match_crowd_data(route_coords)
#         # Find buses covering the route
#         available_buses = find_bus(start_location, end_location)
#
#         return render_template(
#             "result.html",
#             route_coords_json=json.dumps(route_coords),
#             crowd_points_json=json.dumps(crowd_points),
#             buses=available_buses
#         )
#     return render_template("form.html")
# @app.route("/get_buses", methods=["GET"])
# def get_buses():
#     return jsonify([
#         {
#             "bus_number": bus_number,
#             "latitude": bus["lat"],
#             "longitude": bus["lng"]
#         }
#         for bus_number, bus in live_buses.items()
#     ])
# @app.route("/get_route", methods=["POST"])
# def get_route():
#     data = request.get_json()
#     start_location = data.get("start_location")
#     end_location = data.get("end_location")
#
#     start_lat, start_lng = geocode(start_location)
#     end_lat, end_lng = geocode(end_location)
#
#     if start_lat is None or end_lat is None:
#         return jsonify({"error": "Invalid location"}), 400
#
#     route_coords = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng)
#     crowd_points = match_crowd_data(route_coords)
#     available_buses = find_bus(start_location, end_location)
#     initialize_buses_on_route(start_location, end_location)
#
#     return jsonify({
#         "route": route_coords,
#         "crowd": crowd_points,
#         "buses": available_buses
#     })
#
# # --- Endpoint to receive live user locations ---
# # @app.route("/update_location", methods=["POST"])
# # def update_location():
# #     data = request.get_json()
# #     lat = data.get("latitude")
# #     lng = data.get("longitude")
# #     if lat is not None and lng is not None:
# #         live_locations.append({"latitude": lat, "longitude": lng})
# #         return jsonify({"status": "success"})
# #     return jsonify({"status": "error", "message": "Invalid data"}), 400
# #
# #
# # #new change
# #
# # @app.route("/get_locations", methods=["GET"])
# # def get_locations():
# #     print(live_locations)
# #     return jsonify(live_locations)
#
#
# @app.route("/update_location", methods=["POST"])
# def update_location():
#     data = request.get_json()
#     user_id = data.get("user_id")
#     lat = data.get("latitude")
#     lng = data.get("longitude")
#
#     if user_id and lat is not None and lng is not None:
#         # overwrite the location for this user_id
#         live_locations[user_id] = {"latitude": lat, "longitude": lng}
#         return jsonify({"status": "success"})
#
#     return jsonify({"status": "error", "message": "Invalid data"}), 400
# @app.route("/get_locations", methods=["GET"])
# def get_locations():
#     return jsonify([
#         {"user_id": uid, "latitude": loc["latitude"], "longitude": loc["longitude"]}
#         for uid, loc in live_locations.items()
#     ])
#
#
#
# if __name__ == "__main__":
#     threading.Thread(target=move_buses, daemon=True).start()
#     app.run(host="0.0.0.0", port=5000, debug=True)












from flask import Flask, request, jsonify
from flask_cors import CORS
import threading, time, math, requests
import sqlite3
import bcrypt


app = Flask(__name__)
CORS(app)

# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)  # Allow Flutter app to access API

DB_NAME = "users.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- Register ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Enter both fields"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username already exists"}), 409

    conn.close()
    return jsonify({"message": "User registered successfully"}), 201

# ---------------- Login ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Enter both fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401
# -------------------------
# Bus dataset
# -------------------------
buses = [
    {
        "bus_number": "19B",
        "start_stop": "Kelambakkam",
        "end_stop": "Broadway",
        "stops": ["Kelambakkam","Siruseri IT Park","Sholinganallur","Tidel Park",
                  "Rajiv Gandhi Salai","Saidapet","Anna University","Guindy","Broadway"]
    },
    {
        "bus_number": "23C",
        "start_stop": "Thiruvanmiyur",
        "end_stop": "Anna University",
        "stops": ["Thiruvanmiyur","Tidel Park","Rajiv Gandhi Salai","Saidapet","Anna University"]
    },
    {
        "bus_number": "570",
        "start_stop": "Kelambakkam",
        "end_stop": "CMBT",
        "stops": ["Kelambakkam","Sholinganallur","Tidel Park","Rajiv Gandhi Salai",
                  "Saidapet","Anna University","Koyambedu CMBT"]
    }
]

# -------------------------
# Live data
# -------------------------
live_locations = {}  # {"user_id": {"latitude": ..., "longitude": ...}}
live_buses = {}      # {"bus_number": {"lat": ..., "lng": ..., "route_coords": [...], "idx": 0, "eta_to_user_start": ...}}

# -------------------------
# Helper functions
# -------------------------
def normalize(text):
    return text.lower().replace(" ", "")

def stop_matches(user_stop, stop_list):
    user_norm = normalize(user_stop)
    for s in stop_list:
        if user_norm in normalize(s) or normalize(s) in user_norm:
            return True
    return False

def find_bus(start_location, end_location):
    available = []
    for bus in buses:
        stops = bus["stops"]
        if stop_matches(start_location, stops) and stop_matches(end_location, stops):
            start_idx = [i for i, s in enumerate(stops) if stop_matches(start_location, [s])][0]
            end_idx = [i for i, s in enumerate(stops) if stop_matches(end_location, [s])][0]
            if start_idx < end_idx:
                eta = (end_idx - start_idx) * 5  # ETA in minutes
                available.append({
                    "bus_number": bus["bus_number"],
                    "start_stop": bus["start_stop"],
                    "end_stop": bus["end_stop"],
                    "eta_min": eta
                })
    return available

def geocode(location_name):
    try:
        viewbox = "80.17,12.95,80.35,13.15"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{location_name}, Chennai, Tamil Nadu, India",
            "format": "json",
            "limit": 1,
            "bounded": 1,
            "viewbox": viewbox
        }
        headers = {"User-Agent": "WayneoApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=5)
        res.raise_for_status()
        data = res.json()
        if not data:
            return None, None
        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        return lat, lng
    except:
        return None, None

def get_route_from_osrm(start_lat, start_lng, end_lat, end_lng):
    if None in (start_lat, start_lng, end_lat, end_lng):
        return []
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        coords = res.json()["routes"][0]["geometry"]["coordinates"]
        return [(lat, lng) for lng, lat in coords]
    except:
        return []

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda / 2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

def match_crowd_data(route_coords, threshold_km=0.5):
    crowd_points = []
    for lat, lng in route_coords:
        people = sum(
            1 for loc in live_locations.values()
            if haversine(lat, lng, loc["latitude"], loc["longitude"]) <= threshold_km
        )
        if people > 0:
            crowd_points.append({"latitude": lat, "longitude": lng, "count": people})
    return crowd_points

def initialize_buses_on_route(user_start, user_end):
    """
    Initialize buses along their own routes, starting from bus's start_stop.
    """
    buses_on_route = find_bus(user_start, user_end)
    for bus in buses_on_route:
        # Find bus object
        bus_obj = next((b for b in buses if b["bus_number"] == bus["bus_number"]), None)
        if not bus_obj:
            continue

        # Geocode bus start & end stops
        start_lat, start_lng = geocode(bus_obj["start_stop"])
        end_lat, end_lng = geocode(bus_obj["end_stop"])
        if None in (start_lat, start_lng, end_lat, end_lng):
            continue

        route_coords = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng)
        if not route_coords:
            continue

        # Geocode user start to calculate ETA
        user_start_lat, user_start_lng = geocode(user_start)
        if user_start_lat is None:
            eta_min = 0
        else:
            closest_idx = min(range(len(route_coords)),
                              key=lambda i: haversine(user_start_lat, user_start_lng,
                                                      route_coords[i][0], route_coords[i][1]))
            eta_min = (len(route_coords) - closest_idx) * 0.1

        live_buses[bus["bus_number"]] = {
            "route_coords": route_coords,
            "idx": 0,
            "lat": route_coords[0][0],
            "lng": route_coords[0][1],
            "eta_to_user_start": round(eta_min, 1)
        }

def move_buses():
    while True:
        for bus_number, bus in live_buses.items():
            if bus["idx"] < len(bus["route_coords"]) - 1:
                bus["idx"] += 1
                bus["lat"], bus["lng"] = bus["route_coords"][bus["idx"]]
            else:
                bus["idx"] = 0
        time.sleep(2)

# -------------------------
# Flask routes
# -------------------------
@app.route("/get_route", methods=["POST"])
def get_route():
    data = request.get_json()
    src = data.get("start_location")
    dest = data.get("end_location")
    start_lat, start_lng = geocode(src)
    end_lat, end_lng = geocode(dest)
    if None in (start_lat, start_lng, end_lat, end_lng):
        return jsonify({"error": "Invalid location"}), 400

    route_coords = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng)
    crowd_points = match_crowd_data(route_coords)
    available_buses = find_bus(src, dest)
    initialize_buses_on_route(src, dest)

    # Attach ETA
    for b in available_buses:
        bus_live = live_buses.get(b["bus_number"])
        if bus_live:
            b["eta_min"] = bus_live["eta_to_user_start"]

    return jsonify({"route": route_coords, "crowd": crowd_points, "buses": available_buses})

@app.route("/get_buses", methods=["GET"])
def get_buses():
    return jsonify([{"bus_number": bus_number, "latitude": bus["lat"], "longitude": bus["lng"]}
                    for bus_number, bus in live_buses.items()])

@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.get_json()
    user_id = data.get("user_id")
    lat, lng = data.get("latitude"), data.get("longitude")
    if user_id and lat is not None and lng is not None:
        live_locations[user_id] = {"latitude": lat, "longitude": lng}
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route("/get_locations", methods=["GET"])
def get_locations():
    return jsonify([{"user_id": uid, "latitude": loc["latitude"], "longitude": loc["longitude"]}
                    for uid, loc in live_locations.items()])

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    threading.Thread(target=move_buses, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
