fixes = {
    "frontend/src/components/SuerteFormModal.svelte": [
        ("    onSave(payload);\n  }", "    await onSave(payload);\n    submitting = false;\n  }"),
    ],
    "frontend/src/components/UserFormModal.svelte": [
        ("    // Parent handles API call via onSave; resets submitting on completion\n    onSave(payload);\n  }", "    await onSave(payload);\n    submitting = false;\n  }"),
    ],
}

for path, replacements in fixes.items():
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"{path}: Fixed")
        else:
            print(f"{path}: Pattern not found!")
            # Show the context around "onSave"
            idx = content.find("onSave(payload")
            if idx >= 0:
                print(f"  Found at {idx}: ...{content[idx:idx+60]}...")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
