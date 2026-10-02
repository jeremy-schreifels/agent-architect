#!/usr/bin/env python3
"""Deterministic checks for agent-architect packages.

Usage:
  validate.py <package-root> [--state STATE.yaml]   package checks
  validate.py --file <artifact.md>                  per-file checks only

Runs PARSE, SCHEMA, REFERENCES, CONTRACT, KNOWLEDGE, DEPENDENCIES, README and
REGRESSION (structure only). BEST_PRACTICES, SAFETY and CRITERIA are semantic
and are not run here. Prints JSON; exit 1 if any gate FAILs.

The constants below mirror knowledge/schemas.md. Keep them in sync.
"""
import hashlib, json, re, sys
from pathlib import Path
import yaml

COMMON_REQ = ["name", "type", "version", "description", "triggers", "inputs", "outputs"]
COMMON_OPT = ["tools", "dependencies", "optional_dependencies", "status", "deprecation", "non_triggers"]
TYPE_OPT = {"agent": ["safety"], "knowledge": ["knowledge_class"]}
TYPES = ["skill", "agent", "capability", "knowledge"]
SKILL_H = ["Overview", "Inputs", "Outputs", "Capabilities", "Instructions", "Tools",
           "Examples", "Edge Cases", "Error Handling & Safety"]
HEADINGS = {
    "skill": SKILL_H,
    "agent": SKILL_H + ["Operating Modes", "Workflow Logic"],
    "capability": ["Purpose", "Scope", "Inputs", "Outputs", "Dependencies", "Failure Modes",
                   "Error Handling & Safety"],
}
KNOW_STATIC = ["Facts", "Policies", "Guidance", "Provenance"]
KNOW_MANAGED = KNOW_STATIC + ["Freshness", "Conflicts", "Retrieval Hints"]
TAXONOMY = {"INPUT_ERROR", "CONFIGURATION_ERROR", "DEPENDENCY_ERROR", "REFERENCE_ERROR",
            "LOGIC_ERROR", "VALIDATION_ERROR", "DATA_QUALITY_ERROR", "SECURITY_ERROR",
            "AUTHORIZATION_ERROR", "ENVIRONMENT_ERROR", "USER_ACTION_REQUIRED"}
TOOL_REQ = ["name", "purpose", "inputs", "outputs", "permissions", "side_effects",
            "authorization", "failure_modes"]
SIDE_EFFECTS = {"none", "reversible", "irreversible", "high_impact"}
AUTHZ = {"user", "system", "delegated", "none"}
SCEN_REQ = ["id", "target", "type", "input", "expected_behavior", "pass_criteria"]
README_H = ["Purpose", "Quick Start", "Inputs and Outputs", "Architecture", "Capabilities",
            "Limitations", "Files"]
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SKIP_DIRS = {".git", "__pycache__", ".architect"}
GATES = ["PARSE", "SCHEMA", "REFERENCES", "CONTRACT", "KNOWLEDGE", "DEPENDENCIES",
         "README", "REGRESSION"]


class Gate:
    def __init__(self, name):
        self.name, self.na = name, False
        self.f = {"critical": [], "major": [], "minor": []}

    def add(self, sev, msg):
        self.f[sev].append(msg)

    def status(self):
        if self.na:
            return "NOT_APPLICABLE"
        return "FAIL" if self.f["critical"] or self.f["major"] else "PASS"

    def out(self):
        return {"name": self.name, "scope": "package", "status": self.status(), "findings": self.f}


def strict_load(text):
    """YAML load rejecting anchors, aliases, and explicit tags."""
    for ev in yaml.parse(text, Loader=yaml.SafeLoader):
        if isinstance(ev, yaml.AliasEvent):
            raise ValueError("YAML alias not allowed")
        if getattr(ev, "anchor", None):
            raise ValueError("YAML anchor not allowed")
        if getattr(ev, "tag", None):
            raise ValueError("YAML tag not allowed")
    return yaml.safe_load(text)


def split_fm(text):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    return text[4:end], text[end + 5:]


def sections(body, level=1):
    """Map heading -> text, ignoring fenced code blocks."""
    out, cur, fence = {}, None, False
    pat = re.compile(r"^" + "#" * level + r" (.+?)\s*$")
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else pat.match(line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def fenced_yaml(text):
    return re.findall(r"```yaml\n(.*?)```", text, re.S)


def paths_in(text):
    return set(re.findall(r"`((?:knowledge|capabilities|scripts|tests|examples)/[A-Za-z0-9_./-]+)`", text))


def sha(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def load_artifact(path, root_names):
    text = path.read_text(encoding="utf-8")
    fm_text, body = split_fm(text)
    fm = strict_load(fm_text)
    if not isinstance(fm, dict):
        raise ValueError("frontmatter is not a mapping")
    return fm, body


def check_file(rel, fm, body, g, expected_type=None):
    """PARSE-independent per-file checks: SCHEMA and CONTRACT."""
    S, C = g["SCHEMA"], g["CONTRACT"]
    t = fm.get("type")
    for k in COMMON_REQ:
        if k not in fm:
            S.add("major", f"{rel}: missing field {k}")
    if t not in TYPES:
        S.add("major", f"{rel}: invalid type {t!r}")
        return
    if expected_type and t not in expected_type:
        S.add("major", f"{rel}: type {t} not allowed here")
    allowed = set(COMMON_REQ + COMMON_OPT + TYPE_OPT.get(t, []))
    for k in fm:
        if k not in allowed:
            S.add("major", f"{rel}: undeclared field {k}")
    if not SEMVER.match(str(fm.get("version", ""))):
        S.add("major", f"{rel}: version is not SemVer")
    if fm.get("status", "active") not in ("active", "deprecated"):
        S.add("major", f"{rel}: invalid status")
    if (fm.get("status") == "deprecated") != ("deprecation" in fm):
        S.add("major", f"{rel}: deprecation block required iff status is deprecated")
    h = sections(body)
    if t == "knowledge":
        need = KNOW_STATIC if fm.get("knowledge_class") == "static" else KNOW_MANAGED
        if fm.get("knowledge_class", "managed") not in ("static", "managed"):
            S.add("major", f"{rel}: invalid knowledge_class")
    else:
        need = list(HEADINGS[t])
        if t == "capability" and fm.get("tools"):
            need.append("Tools")
    for x in need:
        if x not in h:
            S.add("major", f"{rel}: missing heading {x}")
    # CONTRACT: inputs/outputs identifiers appear in their sections
    for key, sec in (("inputs", "Inputs"), ("outputs", "Outputs")):
        for item in fm.get(key) or []:
            if re.fullmatch(r"[a-z][a-z0-9_]*", str(item)) and sec in h and item not in h[sec]:
                C.add("major", f"{rel}: frontmatter {key} item {item} not in '{sec}' section")
    # CONTRACT: tools
    declared = list(fm.get("tools") or [])
    contracts = []
    if "Tools" in h:
        for blk in fenced_yaml(h["Tools"]):
            try:
                v = strict_load(blk)
                contracts += v if isinstance(v, list) else []
            except Exception as e:
                C.add("major", f"{rel}: Tools YAML invalid: {e}")
    names = [c.get("name") for c in contracts if isinstance(c, dict)]
    if sorted(names) != sorted(declared):
        C.add("major", f"{rel}: tools {declared} do not match Tool Contracts {names}")
    for c in contracts:
        if not isinstance(c, dict):
            continue
        for k in TOOL_REQ:
            if k not in c:
                C.add("major", f"{rel}: tool {c.get('name')} missing {k}")
        if c.get("side_effects") not in SIDE_EFFECTS:
            C.add("major", f"{rel}: tool {c.get('name')} invalid side_effects")
        if c.get("authorization") not in AUTHZ:
            C.add("major", f"{rel}: tool {c.get('name')} invalid authorization")
        for e in c.get("failure_modes") or []:
            if e not in TAXONOMY:
                C.add("major", f"{rel}: tool {c.get('name')} failure mode {e} not in taxonomy")
    # CONTRACT: error tokens anywhere in the file
    for tok in sorted(set(re.findall(r"\b[A-Z]+(?:_[A-Z]+)*_ERROR\b", body))):
        if tok not in TAXONOMY:
            C.add("major", f"{rel}: error token {tok} not in taxonomy")
    # CONTRACT: capability Dependencies heading mirrors frontmatter
    if t == "capability" and "Dependencies" in h:
        fm_deps = set(fm.get("dependencies") or []) | set(fm.get("optional_dependencies") or [])
        if paths_in(h["Dependencies"]) != fm_deps:
            C.add("major", f"{rel}: Dependencies heading differs from frontmatter")
    if t in ("skill", "agent") and "Capabilities" in h:
        fm_deps = set(fm.get("dependencies") or []) | set(fm.get("optional_dependencies") or [])
        for p in paths_in(h["Capabilities"]):
            if p not in fm_deps:
                C.add("major", f"{rel}: capability {p} used but not a declared dependency")


def check_package(root, state_path):
    g = {n: Gate(n) for n in GATES}
    files = sorted(p for p in root.rglob("*")
                   if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_DIRS))
    rels = [str(p.relative_to(root)) for p in files]
    hashes = {r: sha(p.read_bytes()) for r, p in zip(rels, files)}
    pkg_hash = sha("\n".join(f"{r}:{hashes[r]}" for r in sorted(rels)).encode())

    root_file = next((r for r in ("agent.md", "skill.md") if r in rels), None)
    arts = {}
    if root_file is None:
        g["SCHEMA"].add("critical", "no agent.md or skill.md at package root")
    candidates = ([root_file] if root_file else []) + \
        [r for r in rels if r.startswith(("capabilities/", "knowledge/")) and r.endswith(".md")]
    for r in candidates:
        try:
            arts[r] = load_artifact(root / r, None)
        except Exception as e:
            g["PARSE"].add("critical", f"{r}: {e}")
    scen = None
    if "tests/scenarios.yaml" in rels:
        try:
            scen = strict_load((root / "tests/scenarios.yaml").read_text(encoding="utf-8"))
        except Exception as e:
            g["PARSE"].add("critical", f"tests/scenarios.yaml: {e}")

    for r, (fm, body) in arts.items():
        exp = ["skill", "agent"] if r == root_file else \
              ["capability"] if r.startswith("capabilities/") else ["knowledge"]
        check_file(r, fm, body, g, exp)
        if r != root_file and fm.get("name") != Path(r).stem:
            g["SCHEMA"].add("major", f"{r}: name {fm.get('name')!r} != file stem")

    # REFERENCES + DEPENDENCIES
    graph = {}
    for r, (fm, body) in arts.items():
        deps = list(fm.get("dependencies") or []) + list(fm.get("optional_dependencies") or [])
        graph[r] = [d for d in deps if d in arts]
        for d in deps:
            if d not in rels:
                g["DEPENDENCIES"].add("major", f"{r}: dependency {d} does not exist")
            elif d in arts and arts[d][0].get("status") == "deprecated":
                g["DEPENDENCIES"].add("minor", f"{r}: depends on deprecated {d}")
        for p in paths_in(body):
            if p not in rels:
                g["REFERENCES"].add("major", f"{r}: reference `{p}` does not resolve")
    state_color = {}

    def dfs(n, stack):
        state_color[n] = 1
        for m in graph.get(n, []):
            if state_color.get(m) == 1:
                g["DEPENDENCIES"].add("major", "dependency cycle: " + " -> ".join(stack + [n, m]))
            elif m not in state_color:
                dfs(m, stack + [n])
        state_color[n] = 2
    for n in graph:
        if n not in state_color:
            dfs(n, [])
    # CHANGELOG coverage
    if "CHANGELOG.md" not in rels:
        g["REFERENCES"].add("major", "CHANGELOG.md missing")
    else:
        cl = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        if root_file in arts and not re.search(r"^## " + re.escape(str(arts[root_file][0].get("version"))) + r"\b", cl, re.M):
            g["REFERENCES"].add("major", "CHANGELOG.md has no section for the root artifact version")
        for r, (fm, _) in arts.items():
            if not any(r in ln and str(fm.get("version")) in ln for ln in cl.split("\n")):
                g["REFERENCES"].add("major", f"CHANGELOG.md has no entry for {r} {fm.get('version')}")

    # KNOWLEDGE
    know = [r for r in arts if r.startswith("knowledge/")]
    if not know:
        g["KNOWLEDGE"].na = True
    for r in know:
        fm, body = arts[r]
        if fm.get("knowledge_class") != "static":
            h = sections(body)
            if "```yaml" not in h.get("Facts", ""):
                g["KNOWLEDGE"].add("major", f"{r}: managed knowledge has no Knowledge Entry blocks")

    # README
    if "README.md" not in rels:
        g["README"].na = True
    else:
        txt = (root / "README.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        h2 = sections(txt, 2)
        order = [k for k in h2 if k in README_H]
        if order != README_H:
            g["README"].add("major", f"README headings {order} != canonical order {README_H}")
        rows = [ln for ln in h2.get("Capabilities", "").split("\n") if ln.startswith("|")]
        if rows and [c.strip() for c in rows[0].strip("|").split("|")] != ["Capability", "Description", "Version"]:
            g["README"].add("major", "capability table columns must be Capability, Description, Version")
        table = {}
        for ln in rows[2:]:
            c = [x.strip() for x in ln.strip("|").split("|")]
            if len(c) == 3:
                table[c[0]] = c[2]
        caps = {Path(r).stem: str(fm.get("version")) for r, (fm, _) in arts.items() if r.startswith("capabilities/")}
        if table != caps:
            g["README"].add("major", f"capability table {table} != actual {caps}")
        listed = set(re.findall(r"`([^`]+)`", h2.get("Files", "")))
        for p in listed:
            if not any(r == p or (p.endswith("/") and r.startswith(p)) for r in rels):
                g["README"].add("major", f"Files lists `{p}` which does not exist")
        for r in rels:
            if not any(r == p or (p.endswith("/") and r.startswith(p)) for p in listed):
                g["README"].add("major", f"Files does not list {r}")

    # REGRESSION (structure only)
    if scen is None:
        g["REGRESSION"].na = "tests/scenarios.yaml" not in rels
    else:
        seen = set()
        for s in scen if isinstance(scen, list) else []:
            sid = s.get("id") if isinstance(s, dict) else None
            for k in SCEN_REQ:
                if not isinstance(s, dict) or k not in s:
                    g["REGRESSION"].add("major", f"scenario {sid}: missing {k}")
            if sid in seen:
                g["REGRESSION"].add("major", f"duplicate scenario id {sid}")
            seen.add(sid)
            if isinstance(s, dict):
                if s.get("type") not in ("static", "runtime"):
                    g["REGRESSION"].add("major", f"scenario {sid}: invalid type")
                if s.get("target") not in rels:
                    g["REGRESSION"].add("major", f"scenario {sid}: target {s.get('target')} not found")
        if not isinstance(scen, list):
            g["REGRESSION"].add("major", "scenarios must be a list")

    result = {"artifact_state": {
        "content_hash": pkg_hash,
        "artifacts": [{"path": r, "version": str(arts[r][0].get("version")) if r in arts else None,
                       "content_hash": hashes[r]} for r in rels]}}
    # State: staleness and released immutability
    if state_path:
        st = yaml.safe_load(Path(state_path).read_text(encoding="utf-8")) or {}
        result["state_check"] = {"stale_gates": [], "released_mutations": []}
        for gt in st.get("gates") or []:
            if gt.get("content_hash") and gt["content_hash"] != pkg_hash and gt.get("scope", "package") == "package":
                result["state_check"]["stale_gates"].append(gt.get("name"))
        for a in st.get("artifacts") or []:
            if a.get("lifecycle") == "released" and hashes.get(a.get("path")) != a.get("content_hash"):
                result["state_check"]["released_mutations"].append(a.get("path"))
                g["SCHEMA"].add("critical", f"{a.get('path')}: released artifact changed (LOGIC_ERROR)")
    return g, result


def overall(gates):
    st = [x.status() for x in gates.values() if not x.na]
    for s in ("FAIL", "BLOCKED", "STALE"):
        if s in st:
            return s
    return "PASS" if st else "NOT_APPLICABLE"


def main(argv):
    if len(argv) >= 3 and argv[1] == "--file":
        g = {n: Gate(n) for n in GATES}
        p = Path(argv[2])
        try:
            fm, body = load_artifact(p, None)
            check_file(p.name, fm, body, g)
        except Exception as e:
            g["PARSE"].add("critical", f"{p.name}: {e}")
        gates = {k: v for k, v in g.items() if k in ("PARSE", "SCHEMA", "CONTRACT")}
        result = {}
    elif len(argv) >= 2 and not argv[1].startswith("-"):
        state = argv[argv.index("--state") + 1] if "--state" in argv else None
        gates, result = check_package(Path(argv[1]), state)
    else:
        print(__doc__)
        return 2
    result["gates"] = [x.out() for x in gates.values()]
    result["overall_deterministic"] = overall(gates)
    result["semantic_gates_not_run"] = ["BEST_PRACTICES", "SAFETY", "CRITERIA"]
    print(json.dumps(result, indent=2))
    return 1 if result["overall_deterministic"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
