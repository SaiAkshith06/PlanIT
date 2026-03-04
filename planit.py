"""
PlanIt: Multi-Agent AI Planner (Google Maps Integrated)

This script demonstrates a distributed multi-agent
architecture for trip planning, integrated with Google Maps API.
"""
import os
import json
from datetime import datetime

import urllib.parse
import requests

# Replaced Google Maps with Open Source Routing API (OSRM) and Nominatim Geocoding

# =========================================================
# Base Agent Class
# =========================================================
class BaseAgent:
    def __init__(self, name):
        self.name = name

    def process(self, data):
        raise NotImplementedError("Each agent must implement the process() method")

# =========================================================
# Preference Agent
# =========================================================
class PreferenceAgent(BaseAgent):
    def process(self, user_input):
        print(f"[{self.name}] Processing user preferences (Priority: {user_input['priority']})...")
        weights = {
            "time_weight": 0.8 if user_input["priority"] == "fast" else 0.3,
            "cost_weight": 0.2 if user_input["priority"] == "fast" else 0.7,
        }
        return weights

# =========================================================
# Route Planning Agent (Integrated with Google Maps API)
# =========================================================
class RouteAgent(BaseAgent):
    def process(self, user_input):
        print(f"[{self.name}] Finding routes via Open Source Routing (OSRM)...")
        source = user_input["source"]
        destination = user_input["destination"]
        
        routes = []
        
        # 1. Geocode Locations (Convert text like "Hyderabad" to Lat/Lon via Nominatim)
        def get_coordinates(query):
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
            headers = {"User-Agent": "PlanIt-MultiAgentPlanner/1.0"}
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                if data:
                    return f"{data[0]['lon']},{data[0]['lat']}"
            except Exception as e:
                print(f"[{self.name}] Geocoding Error for {query}: {e}")
            return None

        src_coords = get_coordinates(source)
        dst_coords = get_coordinates(destination)

        if not src_coords or not dst_coords:
            print(f"[{self.name}] Could not geocode source or destination. Using fallback data.")
            routes = [
                {"mode": "driving", "route": f"Simulated Route: {source} to {destination}", "distance_meters": 10000, "time_seconds": 1200, "geometry": None}
            ]
            return {"routes": routes, "user_input": user_input}

        # 2. Get Routing Data from OSRM
        # OSRM public API supports 'car', 'bike', 'foot'
        modes_map = {
            "driving": "car",
            "bicycling": "bike",
            "walking": "foot"
        }
        
        for mode_name, osrm_profile in modes_map.items():
            # Request route with geometry (geojson format) for Leaflet rendering
            osrm_url = f"http://router.project-osrm.org/route/v1/{osrm_profile}/{src_coords};{dst_coords}?overview=full&geometries=geojson"
            
            try:
                response = requests.get(osrm_url)
                if response.status_code == 200:
                    data = response.json()
                    if data["code"] == "Ok" and len(data["routes"]) > 0:
                        route_data = data["routes"][0]
                        distance_meters = route_data["distance"]
                        duration_seconds = route_data["duration"]
                        geometry = route_data["geometry"]
                        
                        # Format for human reading
                        dist_km = distance_meters / 1000
                        dist_text = f"{dist_km:.1f} km"
                        
                        mins = int(duration_seconds // 60)
                        hours = mins // 60
                        mins = mins % 60
                        time_text = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"

                        routes.append({
                            "mode": mode_name,
                            "route": f"via OSRM {mode_name.title()}",
                            "distance_text": dist_text,
                            "distance_meters": distance_meters,
                            "time_text": time_text,
                            "time_seconds": duration_seconds,
                            "geometry": geometry # New: Will pass directly to Leaflet
                        })
            except Exception as e:
                print(f"[{self.name}] OSRM Route Error ({mode_name}): {e}")
                
        # If OSRM fails or specific modes fail, we could fallback, but for now we'll just check if routes is empty
        if not routes:
             routes = [
                {"mode": "driving", "route": "Simulated Highway", "distance_meters": 10000, "time_seconds": 1200, "geometry": None},
                {"mode": "bicycling", "route": "Simulated Bike Path", "distance_meters": 8000, "time_seconds": 3600, "geometry": None},
            ]
        
        return {"routes": routes, "user_input": user_input}

# =========================================================
# Cost Optimization Agent
# =========================================================
class CostAgent(BaseAgent):
    def process(self, data):
        print(f"[{self.name}] Estimating route costs...")
        for r in data["routes"]:
            # Simple cost model depending on mode
            if r["mode"] == "driving":
                # Assuming ₹12 per km for fuel and wear in India
                r["cost"] = (r["distance_meters"] / 1000) * 12.0
            elif r["mode"] == "transit":
                # Flat fare for transit
                r["cost"] = 50.0
            elif r["mode"] in ["bicycling", "walking"]:
                r["cost"] = 0.0  # Free!
            else:
                r["cost"] = (r["distance_meters"] / 1000) * 8.0
                
            r["cost"] = round(r["cost"])
        return data

# =========================================================
# Time Scheduling Agent
# =========================================================
class TimeAgent(BaseAgent):
    def process(self, data):
        print(f"[{self.name}] Evaluating travel times...")
        for r in data["routes"]:
            # Score based on inverse of time (higher is better)
            # Add +1 to avoid division by zero
            r["score_time"] = 10000 / (r["time_seconds"] + 1)
        return data

# =========================================================
# Resource Management Agent
# =========================================================
class ResourceAgent(BaseAgent):
    def process(self, data):
        print(f"[{self.name}] Checking resource feasibility...")
        feasible_routes = []
        for r in data["routes"]:
            # All returned routes from APIs are considered feasible
            r["feasible"] = True
            feasible_routes.append(r)
                
        data["routes"] = feasible_routes
        return data

# =========================================================
# Decision Fusion Module
# =========================================================
class DecisionFusion:
    @staticmethod
    def select_best(routes, weights):
        print("[Fusion] Selecting optimal route based on weights...")
        best_score = -1
        best_route = None

        for r in routes:
            # Normalize time and cost. We want small time/costs to give high scores.
            time_score = 10000 / (r["time_seconds"] + 1)
            cost_score = 10 / (r["cost"] + 0.1) # Add 0.1 to avoid division by zero
            
            score = (weights["time_weight"] * time_score) + (weights["cost_weight"] * cost_score)

            if score > best_score:
                best_score = score
                best_route = r

        return best_route

# =========================================================
# Main Simulation Driver
def run_planit(source, destination, priority):
    user_input = {
        "source": source,
        "destination": destination,
        "priority": priority,
    }

    pref_agent = PreferenceAgent("PreferenceAgent")
    route_agent = RouteAgent("RouteAgent")
    cost_agent = CostAgent("CostAgent")
    time_agent = TimeAgent("TimeAgent")
    resource_agent = ResourceAgent("ResourceAgent")

    # Pipeline
    weights = pref_agent.process(user_input)
    data = route_agent.process(user_input)
    data = cost_agent.process(data)
    data = time_agent.process(data)
    data = resource_agent.process(data)

    best_route = DecisionFusion.select_best(data["routes"], weights)

    return {
        "best_route": best_route,
        "all_routes": data["routes"]
    }

if __name__ == "__main__":
    print("\n🚀 Starting PlanIt Multi-Agent Simulation with OSRM\n")
    print("-" * 50)
    source = input("📍 Enter Source Location: ")
    destination = input("🏁 Enter Destination Location: ")
    while True:
        priority = input("⚡ Enter Priority (fast/cheap): ").strip().lower()
        if priority in ["fast", "cheap"]:
            break
        print("❌ Invalid input. Please enter 'fast' or 'cheap'.")
    print("-" * 50)
    
    result = run_planit(source, destination, priority)
    print("\n✅ OPTIMAL PLAN GENERATED:")
    import json
    print(json.dumps(result["best_route"], indent=2))