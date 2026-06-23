import glob, urllib.request, re

dist = glob.glob("C:/MySource/sip_edge/frontend/dist/assets/*.js")
static = glob.glob("C:/MySource/sip_edge/src/static/assets/*.js")
print("Dist:", [d.split("/")[-1] for d in dist])
print("Static:", [s.split("/")[-1] for s in static])

resp = urllib.request.urlopen("http://127.0.0.1:8000/")
html = resp.read().decode()
m = re.search(r"src=\"([^\"]+\.js)\"", html)
if m:
    print("Served:", m.group(1).split("/")[-1])

with open(dist[0], "r", encoding="utf-8") as f:
    c = f.read()
print("Nueva Suerte in dist:", "Nueva Suerte" in c)
print("Editar Suerte in dist:", "Editar Suerte" in c)
print()
print("Dist size:", len(c), "bytes")
