import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:5001/api/plan',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({'source': 'Hyderabad', 'destination': 'Mumbai', 'priority': 'fast'}).encode('utf-8')
)

try:
    response = urllib.request.urlopen(req)
    print(json.loads(response.read()))
except Exception as e:
    print(f"Error: {e}")
