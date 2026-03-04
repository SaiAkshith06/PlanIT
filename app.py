from flask import Flask, request, jsonify, render_template

# Try to import the planit script explicitly from the same directory
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    planit = __import__('planit')
except ImportError as e:
    print(f"Error importing planit: {e}")
    planit = None

app = Flask(__name__)

@app.route('/')
def index():
    # Pass the API key to the template so Google Maps JS can load
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    return render_template('index.html', gmaps_key=api_key)

@app.route('/api/plan', methods=['POST'])
def plan_trip():
    data = request.json
    source = data.get('source')
    destination = data.get('destination')
    priority = data.get('priority', 'fast') # default to fast

    if not source or not destination:
        return jsonify({"error": "Source and destination are required"}), 400

    if not planit:
        return jsonify({"error": "PlanIt backend not found"}), 500

    try:
        # Call our refactored multi-agent planning pipeline
        result = planit.run_planit(source, destination, priority)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the server on port 5001 to avoid macOS ControlCenter conflict
    app.run(debug=True, port=5001)
