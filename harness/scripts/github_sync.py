"""
github_sync.py — Syncs feature_list.json features with GitHub Issues.

Usage:
    python harness/scripts/github_sync.py check
    python harness/scripts/github_sync.py create --feature-id 7
    python harness/scripts/github_sync.py close --feature-id 7
    python harness/scripts/github_sync.py comment --feature-id 7 --body "..."

Requires:
    - gh CLI installed and authenticated (gh auth login)
    - harness/github.json with "enabled": true and valid "repo"

Flow:
    create  -> gh issue create, writes issue URL into feature_list.json
    close   -> gh issue close + comment with summary from closure doc
    comment -> gh issue comment (for blocked status updates)
    check   -> verifies gh CLI is installed and authenticated
"""

import json
import subprocess
import sys
from pathlib import Path


def resolve_base():
    """Return the harness/ root (1 level up from harness/scripts/)."""
    return Path(__file__).resolve().parents[1]


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def load_github_config(base):
    cfg_path = base / "github.json"
    if not cfg_path.exists():
        sys.exit(f"[github_sync] ERROR: {cfg_path} not found. Create harness/github.json.")
    return load_json(cfg_path)


def load_features(base):
    fp = base / "feature_list.json"
    if not fp.exists():
        sys.exit(f"[github_sync] ERROR: {fp} not found.")
    return load_json(fp)


def save_features(base, data):
    fp = base / "feature_list.json"
    save_json(fp, data)


def find_feature(features_data, feature_id):
    for feat in features_data["features"]:
        if feat["id"] == feature_id:
            return feat
    sys.exit(f"[github_sync] ERROR: feature id {feature_id} not found in feature_list.json.")


def run_gh(args, check=True):
    """Run gh CLI command. Returns (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            stderr = result.stderr.strip()
            sys.exit(f"[github_sync] ERROR: gh {' '.join(args)} failed: {stderr}")
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        sys.exit("[github_sync] ERROR: gh CLI not found. Install: https://cli.github.com")


def check_available():
    """Verify gh CLI is installed and authenticated."""
    base = resolve_base()
    cfg = load_github_config(base)
    if not cfg.get("enabled"):
        print("[github_sync] WARN: GitHub sync is disabled in harness/github.json (enabled: false)")
        sys.exit(0)

    rc, out, err = run_gh(["auth", "status"], check=False)
    if rc != 0:
        sys.exit("[github_sync] ERROR: gh is not authenticated. Run: gh auth login")
    print(f"[github_sync] OK: gh authenticated. Repo: {cfg['repo']}")
    return True


def build_issue_title(feat):
    """Build a clean issue title from feature data."""
    feature_id = feat["id"]
    title = feat.get("title", feat.get("name", f"Feature {feature_id}"))
    return f"[{feature_id}] {title}"


def build_issue_body(feat, spec_path=None):
    """Build issue body from feature data and optional spec files."""
    lines = []

    feat_type = feat.get("type", "feature")
    lines.append(feat.get("description", "Sin descripcion."))
    lines.append("")

    if feat_type == "bug":
        reproduction = feat.get("reproduction", "")
        if reproduction:
            lines.append("## Reproduction")
            lines.append(reproduction)
            lines.append("")

        affected = feat.get("affected_feature_ids", [])
        if affected:
            lines.append(f"**Affected features:** {', '.join(f'#{d}' for d in affected)}")
            lines.append("")

        lines.append(f"**Type:** bug")
        lines.append("")
        return "\n".join(lines)

    acceptance = feat.get("acceptance", [])
    if acceptance:
        lines.append("## Acceptance Criteria")
        for ac in acceptance:
            lines.append(f"- [ ] {ac}")
        lines.append("")

    if feat.get("depends_on"):
        deps = feat["depends_on"]
        lines.append(f"**Dependencies:** {', '.join(f'#{d}' for d in deps)}")
        lines.append("")

    if feat.get("milestone"):
        lines.append(f"**Milestone:** {feat['milestone']}")
        lines.append("")

    if feat.get("sdd"):
        lines.append("**SDD:** This feature follows Spec Driven Development.")
        if spec_path:
            lines.append(f"Spec: `{spec_path}`")
        lines.append("")

    return "\n".join(lines)


def cmd_create(feature_id, spec_path=None):
    """Create a GitHub issue for a feature and record the URL."""
    base = resolve_base()
    cfg = load_github_config(base)
    if not cfg.get("enabled"):
        sys.exit("[github_sync] ERROR: GitHub sync is disabled. Set enabled: true in harness/github.json")

    features = load_features(base)
    feat = find_feature(features, feature_id)

    # Idempotent: skip if already has github_issue
    if feat.get("github_issue"):
        print(f"[github_sync] SKIP: feature {feature_id} already has github_issue: {feat['github_issue']}")
        return feat["github_issue"]

    title = build_issue_title(feat)
    body = build_issue_body(feat, spec_path)
    labels = cfg.get("labels", ["enhancement"])

    cmd = [
        "issue", "create",
        "--repo", cfg["repo"],
        "--title", title,
        "--body", body,
    ]
    for label in labels:
        cmd.extend(["--label", label])

    rc, out, err = run_gh(cmd)
    if rc != 0:
        print(f"[github_sync] ERROR: {err}")
        sys.exit(1)

    # gh issue create outputs the URL on stdout
    issue_url = out
    feat["github_issue"] = issue_url
    save_features(base, features)

    print(f"[github_sync] OK: issue created -> {issue_url}")
    return issue_url


def build_closure_comment(feat, closure_path):
    """Build a closure comment from the closure doc if available."""
    lines = []
    lines.append(f"**Status: DONE** — Feature `[{feat['id']}] {feat.get('title', feat.get('name', ''))}` completed.")
    lines.append("")

    if closure_path:
        doc = Path(closure_path)
        if doc.exists():
            lines.append(f"Closure document: `{closure_path}`")
            lines.append("")
            content = doc.read_text(encoding="utf-8")
            # Extract summary (first non-empty paragraph after ## Resumen)
            in_summary = False
            summary_lines = []
            for line in content.split("\n"):
                if line.startswith("## Resumen"):
                    in_summary = True
                    continue
                if in_summary:
                    if line.startswith("##"):
                        break
                    stripped = line.strip()
                    if stripped and not stripped.startswith("<"):
                        summary_lines.append(stripped)
            if summary_lines:
                lines.append("### Summary")
                for sl in summary_lines[:5]:  # max 5 lines
                    lines.append(sl)
                lines.append("")

            # Extract verification section
            in_verif = False
            verif_lines = []
            for line in content.split("\n"):
                if line.startswith("## Verificacion"):
                    in_verif = True
                    continue
                if in_verif:
                    if line.startswith("##"):
                        break
                    stripped = line.strip()
                    if stripped:
                        verif_lines.append(stripped)
            if verif_lines:
                lines.append("### Verification")
                for vl in verif_lines:
                    lines.append(vl)

    lines.append("")
    lines.append("> Auto-closed by harness-sdd github_sync.py")
    return "\n".join(lines)


def cmd_close(feature_id, closure_path=None):
    """Close a GitHub issue with a summary comment."""
    base = resolve_base()
    cfg = load_github_config(base)
    if not cfg.get("enabled"):
        sys.exit("[github_sync] ERROR: GitHub sync is disabled.")

    features = load_features(base)
    feat = find_feature(features, feature_id)

    issue_url = feat.get("github_issue")
    if not issue_url:
        sys.exit(f"[github_sync] ERROR: feature {feature_id} has no github_issue. Create it first.")

    # Extract issue number from URL
    # Format: https://github.com/owner/repo/issues/123
    issue_number = issue_url.rstrip("/").split("/")[-1]
    if not issue_number.isdigit():
        sys.exit(f"[github_sync] ERROR: cannot extract issue number from {issue_url}")

    # 1. Add closure comment
    comment_body = build_closure_comment(feat, closure_path)
    rc, out, err = run_gh([
        "issue", "comment", issue_number,
        "--repo", cfg["repo"],
        "--body", comment_body,
    ])
    if rc != 0:
        print(f"[github_sync] ERROR: {err}")
        sys.exit(1)
    print(f"[github_sync] OK: comment added to issue #{issue_number}")

    # 2. Close the issue
    rc, out, err = run_gh([
        "issue", "close", issue_number,
        "--repo", cfg["repo"],
        "--reason", "completed",
    ])
    if rc != 0:
        print(f"[github_sync] ERROR: {err}")
        sys.exit(1)
    print(f"[github_sync] OK: issue #{issue_number} closed")

    return issue_number


def cmd_comment(feature_id, body):
    """Add a comment to a GitHub issue (e.g. for blocked status)."""
    base = resolve_base()
    cfg = load_github_config(base)
    if not cfg.get("enabled"):
        sys.exit("[github_sync] ERROR: GitHub sync is disabled.")

    features = load_features(base)
    feat = find_feature(features, feature_id)

    issue_url = feat.get("github_issue")
    if not issue_url:
        sys.exit(f"[github_sync] ERROR: feature {feature_id} has no github_issue.")

    issue_number = issue_url.rstrip("/").split("/")[-1]

    rc, out, err = run_gh([
        "issue", "comment", issue_number,
        "--repo", cfg["repo"],
        "--body", body,
    ])
    if rc != 0:
        print(f"[github_sync] ERROR: {err}")
        sys.exit(1)
    print(f"[github_sync] OK: comment added to issue #{issue_number}")
    return issue_number


def main():
    if len(sys.argv) < 2:
        print("Usage: github_sync.py <check|create|close|comment> [options]")
        print("  check")
        print("  create --feature-id <n> [--spec-path <path>]")
        print("  close  --feature-id <n> [--closure-path <path>]")
        print("  comment --feature-id <n> --body <text>")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    def get_arg(name):
        try:
            idx = args.index(name)
            return args[idx + 1]
        except (ValueError, IndexError):
            return None

    if command == "check":
        check_available()
    elif command == "create":
        fid = get_arg("--feature-id")
        if not fid:
            sys.exit("--feature-id required for create")
        spec = get_arg("--spec-path")
        cmd_create(int(fid), spec)
    elif command == "close":
        fid = get_arg("--feature-id")
        if not fid:
            sys.exit("--feature-id required for close")
        closure = get_arg("--closure-path")
        cmd_close(int(fid), closure)
    elif command == "comment":
        fid = get_arg("--feature-id")
        body = get_arg("--body")
        if not fid or not body:
            sys.exit("--feature-id and --body required for comment")
        cmd_comment(int(fid), body)
    else:
        sys.exit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
