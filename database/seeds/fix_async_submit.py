paths = [
    "frontend/src/components/HaciendaFormModal.svelte",
    "frontend/src/components/SuerteFormModal.svelte",
    "frontend/src/components/UserFormModal.svelte",
]

for path in paths:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Remove old error-reset $effect if present
    new_lines = []
    skip_block = False
    for line in lines:
        if "Re-enable buttons when error arrives" in line:
            skip_block = True
            continue
        if skip_block:
            if "});" in line and "$effect" in line:
                continue
            if "});" in line:
                skip_block = False
                continue
            if "$effect" in line or "if (error)" in line or "submitting = false" in line or "{" in line or "}" in line:
                continue
            skip_block = False
        new_lines.append(line)
    content = "".join(new_lines)
    
    # Remove any leftover empty lines from the removal
    content = content.replace("\n\n\n", "\n\n")
    
    # Replace handleSubmit to be async
    content = content.replace(
        "  function handleSubmit() {",
        "  async function handleSubmit() {"
    )
    
    # Add await before onSave and submitting reset after
    content = content.replace(
        "onSave({",
        "await onSave({"
    )
    
    # After the closing of onSave(payload), add submitting = false
    # Find "    });" that closes onSave
    if path == "frontend/src/components/UserFormModal.svelte":
        # UserFormModal has a different pattern
        old_end = """    });
  }
"""
        new_end = """    });
    submitting = false;
  }
"""
    else:
        old_end = """    });
  }
"""
        new_end = """    });
    submitting = false;
  }
"""
    
    content = content.replace(old_end, new_end)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"{path}: Fixed")
