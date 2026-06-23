with open(r"C:\MySource\sip_edge\src\static\assets\index-BwT2s-LU.js", "r", encoding="utf-8") as f:
    content = f.read()

for p in ["Guardando", "Guardar", "submit"]:
    idx = content.find(p)
    if idx >= 0:
        start = max(0, idx - 40)
        end = min(len(content), idx + 60)
        print(f"{p}: ...{content[start:end]}...")
        print()
    else:
        print(f"{p}: NOT FOUND")
        print()

# Find all .svelte component names in bundle
components = ["AdminHaciendas", "HaciendaFormModal", "AdminSuertes", "SuerteFormModal", "AdminUsers", "UserFormModal"]
for c in components:
    if c[:8].lower() in content:
        print(f"{c}: present in bundle")
    else:
        print(f"{c}: NOT in bundle")
