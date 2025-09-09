from flask import Flask, request, render_template, jsonify
import json
from flask_cors import CORS
import requests
import math

app = Flask(__name__)
CORS(app)

#dataset for bus
buses= [
    {
        "bus_number": "19B",
        "start_stop": "Kelambakkam",
        "end_stop": "Broadway",
        "stops": [
            "Kelambakkam",
            "Siruseri IT Park",
            "Sholinganallur",
            "Tidel Park",
            "Rajiv Gandhi Salai",
            "Saidapet",
            "Anna University",
            "Guindy",
            "Broadway"
        ]
    },
    {
        "bus_number": "23C",
        "start_stop": "Thiruvanmiyur",
        "end_stop": "Anna University",
        "stops": [
            "Thiruvanmiyur",
            "Tidel Park",
            "Rajiv Gandhi Salai",
            "Saidapet",
            "Anna University"
        ]
    },
    {
        "bus_number": "570",
        "start_stop": "Kelambakkam",
        "end_stop": "CMBT",
        "stops": [
            "Kelambakkam",
            "Sholinganallur",
            "Tidel Park",
            "Rajiv Gandhi Salai",
            "Saidapet",
            "Anna University",
            "Koyambedu CMBT"
        ]
    }
]


# In-memory store for live user locations
live_locations = []  # list of {"latitude": ..., "longitude": ...}




def normalize(text):
    return text.lower().replace(" ", "")


@app.route('/set_route', methods=['POST'])
def set_route():
    data = request.get_json()
    source = data.get("source")
    destination = data.get("destination")
    print("User chose:", source, "->", destination)
    # Save to session/global/db as needed
    return jsonify({"status": "ok", "source": source, "destination": destination})


def stop_matches(user_stop, stop_list):
    user_norm = normalize(user_stop)
    for s in stop_list:
        if user_norm in normalize(s) or normalize(s) in user_norm:
            return True
    return False


# --- Geocoding function: location name -> coordinates ---


def geocode(location_name):
    """
    Geocode a location in Chennai using Nominatim with bounding box and single q parameter.
    Returns (latitude, longitude) or (None, None) if not found.
    """

    # Chennai bounding box: left, bottom, right, top
    viewbox = "80.17,12.95,80.35,13.15"

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{location_name}, Chennai, Tamil Nadu, India",  # single q string
        "format": "json",
        "limit": 1,
        "bounded": 1,
        "viewbox": viewbox
    }
    headers = {"User-Agent": "WayneoApp/1.0 (asifalekha@gmail.com)"}  # REQUIRED

    res = requests.get(url, params=params, headers=headers)
    res.raise_for_status()
    data = res.json()

    if not data:
        return None, None

    # Extract coordinates
    lat = float(data[0]["lat"])
    lng = float(data[0]["lon"])

    # Optional: confirm the returned city is Chennai
    address = data[0].get("display_name", "")
    if "Chennai" not in address:
        return None, None

    return lat, lng




# --- Get route from OSRM ---
def get_route_from_osrm(start_lat, start_lng, end_lat, end_lng):
    url = f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()
    coords = data["routes"][0]["geometry"]["coordinates"]
    # Convert lng, lat → lat, lng
    return [(lat, lng) for lng, lat in coords]


# --- Haversine distance ---
def haversine(lat1, lng1, lat2, lng2):
    R = 6371  # km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # distance in km


#finding the bus in the certain route
def find_bus(start_location, end_location):
    available = []
    for bus in buses:
        stops = bus["stops"]

        if stop_matches(start_location, stops) and stop_matches(end_location, stops):
            start_idx = [i for i, s in enumerate(stops) if stop_matches(start_location, [s])][0]
            end_idx = [i for i, s in enumerate(stops) if stop_matches(end_location, [s])][0]

            if start_idx < end_idx:  # ensure direction is valid
                # Estimate ETA: assume 5 min per stop + crowd delay
                eta = (end_idx - start_idx) * 5
                available.append({
                    "bus_number": bus["bus_number"],
                    "start_stop": bus["start_stop"],
                    "end_stop": bus["end_stop"],
                    "eta_min": eta
                })
    return available



# --- Match crowd along route ---
# def match_crowd_data(route_coords):
#     matched_points = []
#     for lat, lng in route_coords:
#         # count number of live users within 0.05 km (~50 meters)
#         people = sum(
#             1 for loc in live_locations if haversine(lat, lng, loc["latitude"], loc["longitude"]) < 1.8
#         )
#         dots = math.ceil(people / 1)  # 1 dot per person
#         matched_points.append({
#             "latitude": float(lat),
#             "longitude": float(lng),
#             "people_count": people,
#             "dots": int(dots)
#         })
#     return matched_points
#


##new crowd
def match_crowd_data(route_coords, threshold_km=0.05):
    matched_points = []
    for lat, lng in route_coords:
        # Only count users within `threshold_km` of this route point
        people = sum(
            1 for loc in live_locations
            if haversine(lat, lng, loc["latitude"], loc["longitude"]) <= threshold_km
        )
        if people > 0:  # Only add points where someone is actually present
            matched_points.append({
                "latitude": float(lat),
                "longitude": float(lng),
                "people_count": people,
                "dots": people
            })
    return matched_points

# --- Home page: enter start/end locations ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        start_location = request.form["start_location"]
        end_location = request.form["end_location"]

        start_lat, start_lng = geocode(start_location)
        end_lat, end_lng = geocode(end_location)

        if start_lat is None or end_lat is None:
            return "Could not find one of the locations. Please try again."

        route_coords = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng)
        crowd_points = match_crowd_data(route_coords)
        # Find buses covering the route
        available_buses = find_bus(start_location, end_location)

        return render_template(
            "result.html",
            route_coords_json=json.dumps(route_coords),
            crowd_points_json=json.dumps(crowd_points),
            buses=available_buses
        )
    return render_template("form.html")

@app.route("/get_route", methods=["POST"])
def get_route():
    data = request.get_json()
    start_location = data.get("start_location")
    end_location = data.get("end_location")

    start_lat, start_lng = geocode(start_location)
    end_lat, end_lng = geocode(end_location)

    if start_lat is None or end_lat is None:
        return jsonify({"error": "Invalid location"}), 400

    route_coords = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng)
    crowd_points = match_crowd_data(route_coords)
    available_buses = find_bus(start_location, end_location)

    return jsonify({
        "route": route_coords,
        "crowd": crowd_points,
        "buses": available_buses
    })

# --- Endpoint to receive live user locations ---
@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.get_json()
    lat = data.get("latitude")
    lng = data.get("longitude")
    if lat is not None and lng is not None:
        live_locations.append({"latitude": lat, "longitude": lng})
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid data"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)