import re

FILES = [
    "frontend/src/components/HaciendaFormModal.svelte",
    "frontend/src/components/SuerteFormModal.svelte",
    "frontend/src/components/UserFormModal.svelte",
]

MARKER = "  // Reset form when modal opens (reactive to show)"
ADDITION = """  // Re-enable buttons when error arrives from parent (e.g. 409)
  $effect(() => {
    if (error) {
      submitting = false;
    }
  });"""

for path in FILES:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if the fix is already there
    if '// Re-enable buttons when error arrives from parent' in content:
        print(f"{path}: Already fixed, skipping")
        continue
    
    # Find the closing of the first $effect
    # The pattern is: after "  });" that closes the first $effect, add our new one
    # Look for the first occurrence of "  });" after "$effect"
    
    idx = content.find(MARKER)
    if idx < 0:
        print(f"{path}: Marker not found")
        continue
    
    # Find the closing "  });" of this $effect
    close_pos = content.find("  });", idx)
    if close_pos < 0:
        print(f"{path}: Closing not found")
        continue
    
    close_pos += 6  # length of "  });\n"
    
    new_content = content[:close_pos] + "\n" + ADDITION + content[close_pos:]
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"{path}: Fixed - added error-reset $effect")
