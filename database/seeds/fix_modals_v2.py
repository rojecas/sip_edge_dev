import re

FILES = {
    "frontend/src/components/HaciendaFormModal.svelte": (
        """  onMount(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && hacienda) {
        form = {
          codigo: hacienda.codigo || "",
          nombre: hacienda.nombre || "",
        };
      } else {
        form = { codigo: "", nombre: "" };
      }
    }
  });""",
        """  $effect(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && hacienda) {
        form = {
          codigo: hacienda.codigo || "",
          nombre: hacienda.nombre || "",
        };
      } else {
        form = { codigo: "", nombre: "" };
      }
    }
  });"""
    ),
    "frontend/src/components/SuerteFormModal.svelte": (
        """  onMount(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && suerte) {
        form = {
          hacienda_id: suerte.hacienda_id || haciendaId || 0,
          codigo_suerte: suerte.codigo_suerte || "",
        };
      } else {
        form = {
          hacienda_id: haciendaId || 0,
          codigo_suerte: "",
        };
      }
    }
  });""",
        """  $effect(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && suerte) {
        form = {
          hacienda_id: suerte.hacienda_id || haciendaId || 0,
          codigo_suerte: suerte.codigo_suerte || "",
        };
      } else {
        form = {
          hacienda_id: haciendaId || 0,
          codigo_suerte: "",
        };
      }
    }
  });"""
    ),
}

for path, (old, new_text) in FILES.items():
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new_text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed: {path}")
    else:
        print(f"Pattern not found in: {path}")
        idx = content.find("onMount")
        if idx >= 0:
            print(f"  onMount found at position {idx}")
            print(f"  Context: {content[idx:idx+80]}")
        else:
            print("  No onMount found (already fixed?)")
