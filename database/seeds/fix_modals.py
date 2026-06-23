path = "frontend/src/components/UserFormModal.svelte"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """  // Reset form when modal opens or mode/user changes
  onMount(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && user) {
        form = {
          username: user.username || "",
          password: "",
          full_name: user.full_name || "",
          document: user.document || "",
          role: user.role || "operator",
          is_active: user.is_active !== undefined ? user.is_active : true,
          new_password: "",
        };
      } else {
        form = {
          username: "",
          password: "",
          full_name: "",
          document: "",
          role: "operator",
          is_active: true,
          new_password: "",
        };
      }
    }
  });"""

new_block = """  // Reset form when modal opens (reactive to show)
  $effect(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && user) {
        form = {
          username: user.username || "",
          password: "",
          full_name: user.full_name || "",
          document: user.document || "",
          role: user.role || "operator",
          is_active: user.is_active !== undefined ? user.is_active : true,
          new_password: "",
        };
      } else {
        form = {
          username: "",
          password: "",
          full_name: "",
          document: "",
          role: "operator",
          is_active: true,
          new_password: "",
        };
      }
    }
  });"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print("UserFormModal: onMount -> $effect OK")
else:
    print("UserFormModal: Pattern not found!")
    # Debug: show the actual onMount block
    idx = content.find("onMount")
    if idx >= 0:
        print("Found at", idx)
        print(content[idx:idx+500])

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
