import requests
import sys

def check(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print(f"✅ {url} - OK")
        else:
            print(f"❌ {url} - Status {r.status_code}")
    except Exception as e:
        print(f"❌ {url} - Error: {e}")

urls = [
    "http://127.0.0.1:8000/",
    "http://127.0.0.1:8000/persons",
    "http://127.0.0.1:8000/works",
    "http://127.0.0.1:8000/scholarly",
    "http://127.0.0.1:8000/places",
    "http://127.0.0.1:8000/map",
    "http://127.0.0.1:8000/network",
    "http://127.0.0.1:8000/api/geojson",
    "http://127.0.0.1:8000/api/network"
]

print("Verifying Endpoints...")
for u in urls:
    check(u)
