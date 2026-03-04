# PlanIT

PlanIt is a web-based multi-agent AI system that generates optimized travel routes between locations based on user preferences such as **fastest route** or **cheapest route**.

The system uses a **distributed agent architecture** where different agents handle route discovery, cost estimation, time evaluation, and decision-making. The final optimal route is selected through a **decision fusion module**.

The project also includes an interactive web interface where users can input source and destination locations and visualize route options.

---

## Features

* Multi-agent architecture for route planning
* Web-based interactive interface
* Route optimization based on **time or cost preference**
* Integration with **Open Source Routing Machine (OSRM)**
* Location geocoding using **OpenStreetMap Nominatim API**
* Visualization using **Leaflet maps**
* Automatic evaluation of multiple travel modes:

  * Driving
  * Cycling
  * Walking

---

## System Architecture

The system is composed of multiple specialized agents:

1. **Preference Agent**

   * Interprets user priority (fast or cheap)
   * Generates weights for decision making

2. **Route Agent**

   * Retrieves routes between locations
   * Uses OSRM routing service

3. **Cost Agent**

   * Calculates estimated travel cost

4. **Time Agent**

   * Evaluates travel duration

5. **Resource Agent**

   * Verifies route feasibility

6. **Decision Fusion Module**

   * Combines all agent outputs
   * Selects the optimal route

---

## Project Structure

```
PlanIt-Multi-Agent-Planner
│
├── app.py                # Flask backend server
├── planit.py             # Multi-agent planning system
├── test_api.py           # API testing script
├── requirements.txt      # Python dependencies
├── README.md
│
├── templates
│   └── index.html        # Web interface
│
└── static
    ├── styles.css        # UI styling
    └── main.js           # Frontend logic
```

---

## Technology Stack

Backend

* Python
* Flask

Frontend

* HTML
* CSS
* JavaScript

APIs and Libraries

* OSRM Routing API
* OpenStreetMap Nominatim Geocoding
* Leaflet.js for map visualization

---

## Installation

Clone the repository

```
git clone https://github.com/your-username/PlanIt-Multi-Agent-Planner.git
```

Navigate to the project directory

```
cd PlanIt-Multi-Agent-Planner
```

Install dependencies

```
pip install -r requirements.txt
```

---

## Running the Application

Start the Flask server

```
python app.py
```

Open your browser and go to:

```
http://127.0.0.1:5001
```

---

## Example Usage

Input

Source: Hyderabad
Destination: Mumbai
Priority: Fastest Route

Output

* Multiple routes evaluated by agents
* Optimal route selected using weighted decision model
* Route displayed on map with distance and time estimates

---

## API Endpoint

```
POST /api/plan
```

Example Request

```
{
  "source": "Hyderabad",
  "destination": "Mumbai",
  "priority": "fast"
}
```

---

## Future Improvements

* Deploy the system online
* Add public transport routing
* Integrate real-time traffic data
* Improve route visualization
* Extend agent collaboration strategies

---

## Author

Sai Akshith

---

## License

This project is for academic and educational purposes.

