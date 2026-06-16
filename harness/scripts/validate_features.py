"""
validate_features.py — Validates feature_list.json structure.

Checks:
- All required fields present (id, name, status)
- type field: "feature" (default) or "bug"
- Valid status values (per type)
- No duplicate IDs
- If type="bug": reproduction and affected_feature_ids required
- If type="bug": affected_feature_ids must reference existing IDs
- If type="feature" and sdd=true: acceptance criteria must be present
- If github_issue is present, must be a valid GitHub URL
"""
import json
import re
import sys
from pathlib import Path

VALID_TYPES = {"feature", "bug"}
VALID_STATUSES = {"pending", "spec_ready", "in_progress", "done", "blocked", "untriaged", "triaged"}
FEATURE_ONLY_STATUSES = {"pending", "spec_ready"}
BUG_ONLY_STATUSES = {"untriaged", "triaged"}
BUG_REQUIRED_FIELDS = {"reproduction", "affected_feature_ids"}
FEATURE_REQUIRED_FIELDS = {"id", "name", "status"}
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
    all_ids = {feat["id"] for feat in features if isinstance(feat, dict) and "id" in feat}

    for i, feat in enumerate(features):
        prefix = f"feature[{i}]"

        if not isinstance(feat, dict):
            errors.append(f"{prefix}: not an object")
            continue

        missing = FEATURE_REQUIRED_FIELDS - set(feat.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {missing}")

        feat_type = feat.get("type", "feature")
        if feat_type not in VALID_TYPES:
            errors.append(f"{prefix}: invalid type '{feat_type}'. Must be one of {VALID_TYPES}")

        status = feat.get("status", "")
        if status not in VALID_STATUSES:
            errors.append(f"{prefix}: invalid status '{status}'")
        elif status in FEATURE_ONLY_STATUSES and feat_type == "bug":
            errors.append(f"{prefix}: bug cannot have status '{status}'. Bug statuses: untriaged, triaged, in_progress, done, blocked")
        elif status in BUG_ONLY_STATUSES and feat_type != "bug":
            errors.append(f"{prefix}: status '{status}' is only valid for bugs (type: bug)")

        fid = feat.get("id")
        if fid in seen_ids:
            errors.append(f"{prefix}: duplicate id '{fid}'")
        seen_ids.add(fid)

        if feat_type == "bug":
            for field in BUG_REQUIRED_FIELDS:
                if field not in feat:
                    errors.append(f"{prefix}: bug missing required field '{field}'")
            reproduction = feat.get("reproduction")
            if reproduction is not None and (not isinstance(reproduction, str) or not reproduction.strip()):
                errors.append(f"{prefix}: reproduction must be a non-empty string")
            affected = feat.get("affected_feature_ids")
            if isinstance(affected, list):
                for afid in affected:
                    if afid not in all_ids:
                        errors.append(f"{prefix}: affected_feature_ids references non-existent id '{afid}'")
            else:
                if affected is not None:
                    errors.append(f"{prefix}: affected_feature_ids must be an array of integers")

        if feat_type == "feature":
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
    base = Path(__file__).resolve().parents[1]  # harness/ (from harness/scripts/)
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
