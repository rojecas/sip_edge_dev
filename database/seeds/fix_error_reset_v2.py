import sys
sys.stdout.reconfigure(encoding="utf-8")

for path in [
    r"frontend/src/components/HaciendaFormModal.svelte",
    r"frontend/src/components/SuerteFormModal.svelte",
]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Check if already fixed
    already_fixed = any("error-reset" in line for line in lines)
    if already_fixed:
        print(f"{path}: Already fixed")
        continue
    
    # Find lines with $effect
    effect_idx = -1
    for i, line in enumerate(lines):
        if "$effect" in line:
            effect_idx = i
            break
    
    if effect_idx < 0:
        print(f"{path}: No $effect found")
        continue
    
    # Track brace depth to find closing
    brace_count = 0
    started = False
    insert_after = -1
    for i in range(effect_idx, len(lines)):
        line = lines[i]
        if not started:
            started = True
            brace_count = 0
            for c in line:
                if c == "{": brace_count += 1
                if c == "}": brace_count -= 1
            continue
        for c in line:
            if c == "{": brace_count += 1
            if c == "}": brace_count -= 1
        if brace_count <= 0:
            insert_after = i + 1
            break
    
    if insert_after > 0:
        addition = [
            "\n",
            "  // Re-enable buttons when error arrives from parent (e.g. 409)\n",
            "  $effect(() => {\n",
            "    if (error) {\n",
            "      submitting = false;\n",
            "    }\n",
            "  });\n",
        ]
        for j, a in enumerate(addition):
            lines.insert(insert_after + j, a)
        
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"{path}: Fixed")
    else:
        print(f"{path}: Could not find insertion point")
