import urllib.request
import json
import sys

print("--- VERIFICACIÓN HTTP DE ULTRARENTABLE ---")
urls = [
    "http://127.0.0.1:3000/pro/ultrarentable/prop-firms",
    "http://127.0.0.1:3000/prop-firms",
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"[OK] {url} -> Status {response.status}")
    except Exception as e:
        print(f"[NOTE] {url} -> {e}")

print("Verificación de rutas completada.")
