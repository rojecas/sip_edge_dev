import urllib.request, re
resp = urllib.request.urlopen("http://127.0.0.1:8000/")
html = resp.read().decode()
m = re.search(r"src=\"([^\"]+\.js)\"", html)
if m:
    url = m.group(1)
    filename = url.split("/")[-1]
    print(f"Bundle served: {filename}")
    
    # Fetch the JS and check for the fix
    js_resp = urllib.request.urlopen("http://127.0.0.1:8000" + ("" if url.startswith("/") else "/") + url)
    js = js_resp.read().decode("utf-8")
    
    # Check for async submit pattern
    if "submitting = false" in js:
        print("submitting = false: PRESENT")
    else:
        print("submitting = false: NOT FOUND")
    
    if "await onSave" in js or "await onSave" in js:
        print("await onSave: PRESENT")
    else:
        print("await onSave: NOT FOUND")
else:
    print("No JS bundle found")
