files = {
    "src/haciendas.py": [
        ('"Hacienda with this codigo already exists"', '"Ya existe una hacienda con este codigo. Cambielo para poder guardarla."'),
        ('"Suerte with this codigo already exists in this hacienda"', '"Ya existe una suerte con este codigo en esta hacienda. Cambielo para poder guardarla."'),
    ],
    "src/users.py": [
        ('"Username already exists"', '"Ya existe un usuario con este nombre. Elija otro nombre para poder guardarlo."'),
    ],
}

for path, replacements in files.items():
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            print(f"{path}: Replaced {count} occurrence(s)")
        else:
            print(f"{path}: '{old}' not found!")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
print("Done")
