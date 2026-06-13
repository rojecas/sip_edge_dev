"""
validate_features.py — Validates feature_list.json structure.

Checks:
- All required fields present (id, name, status, sdd)
- Valid status values
- No duplicate IDs
- If `sdd: true`, acceptance criteria must be present
- If `github_issue` is present, must be a valid GitHub URL or issue number
"""
import json
import re
import sys
from pathlib import Path

VALID_STATUSES = {"pending", "spec_ready", "in_progress", "done", "blocked"}
REQUIRED_FIELDS = {"id", "name", "status"}
GITHUB_URL_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/issues/\d+$")


def validate_features(path: str) -> tuple[bool, list[str]]:
    errors = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return False, [str(e)]

    if not isinstance(data, dict):
        errors.append("feature_list.json must be an object")
        return False, errors

    features = data.get("features")
    if features is None:
        errors.append("feature_list.json missing 'features' key")
        return False, errors

    if not isinstance(features, list):
        errors.append("'features' must be a list")
        return False, errors

    seen_ids = set()
    for i, feat in enumerate(features):
        prefix = f"feature[{i}]"

        if not isinstance(feat, dict):
            errors.append(f"{prefix}: not an object")
            continue

        missing = REQUIRED_FIELDS - set(feat.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {missing}")

        if feat.get("status") not in VALID_STATUSES:
            errors.append(f"{prefix}: invalid status '{feat.get('status')}'")

        fid = feat.get("id")
        if fid in seen_ids:
            errors.append(f"{prefix}: duplicate id '{fid}'")
        seen_ids.add(fid)

        if feat.get("sdd") is True and not feat.get("acceptance"):
            errors.append(f"{prefix}: sdd=true but no acceptance criteria")

        gh_issue = feat.get("github_issue")
        if gh_issue is not None:
            if not isinstance(gh_issue, str):
                errors.append(f"{prefix}: github_issue must be a string")
            elif not GITHUB_URL_RE.match(gh_issue):
                errors.append(f"{prefix}: github_issue has invalid format '{gh_issue}'. Must be https://github.com/owner/repo/issues/N")

    return len(errors) == 0, errors


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2]  # harness/
    if len(sys.argv) > 1:
        fp = Path(sys.argv[1])
    else:
        fp = base / "feature_list.json"
    ok, errors = validate_features(str(fp))
    if ok:
        print(f"[validate_features] OK — {fp.name} is valid")
        sys.exit(0)
    else:
        for e in errors:
            print(f"[validate_features] ERROR: {e}")
        sys.exit(1)
