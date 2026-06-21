import requests, os

NVIDIA_API_KEY = "your_key_here"

r = requests.get(
    "https://integrate.api.nvidia.com/v1/models",
    headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"}
)
models = r.json().get("data", [])
for m in models:
    print(m["id"])