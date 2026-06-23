import urllib.request, re
resp = urllib.request.urlopen("http://127.0.0.1:8000/")
html = resp.read().decode("utf-8")
print("Status:", resp.status)
import re
src_match = re.search(r"src=[\"']([^\"']+\.js)[\"']", html)
if src_match:
    js_url = src_match.group(1)
    if not js_url.startswith("http"):
        js_url = "http://127.0.0.1:8000" + ("" if js_url.startswith("/") else "/") + js_url
    print(f"JS URL: {js_url}")
    js = urllib.request.urlopen(js_url).read().decode("utf-8")
    print(f"JS size: {len(js)} bytes")
    if "Array.isArray(result)" in js:
        print("Array.isArray: PRESENT in bundle")
    else:
        print("Array.isArray: NOT in bundle - OLD VERSION")
else:
    print("No JS bundle found")
print("Done")
