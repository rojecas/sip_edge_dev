import re

with open("tests/test_haciendas.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '"Hacienda with this codigo already exists"',
    '"Ya existe una hacienda con este codigo. Cambielo para poder guardarla."'
)
content = content.replace(
    '"Suerte with this codigo already exists in this hacienda"',
    '"Ya existe una suerte con este codigo en esta hacienda. Cambielo para poder guardarla."'
)

with open("tests/test_haciendas.py", "w", encoding="utf-8") as f:
    f.write(content)
print("test_haciendas.py: Updated")

with open("tests/test_users.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '"Username already exists"',
    '"Ya existe un usuario con este nombre. Elija otro nombre para poder guardarlo."'
)

with open("tests/test_users.py", "w", encoding="utf-8") as f:
    f.write(content)
print("test_users.py: Updated")
