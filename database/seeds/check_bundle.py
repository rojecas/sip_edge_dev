import os, sys
path = r"C:\MySource\sip_edge\src\static\assets\index-BwT2s-LU.js"
size = os.path.getsize(path)
print(f"Size: {size} bytes")
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
print(f"Has hacienda: {'hacienda' in content}")
print(f"Has Hacienda: {'Hacienda' in content}")
print(f"Has submitting: {'submitting' in content}")
for word in ['hacienda', 'Hacienda', 'submitting', 'Guardar', 'Cancelar', '409']:
    count = content.count(word)
    if count > 0:
        print(f"  {word}: {count} occurrences")
if 'hacienda' not in content:
    print("WARNING: HaciendaFormModal code NOT found in bundle!")
    print(f"Content sample: {content[15000:16000]}")
