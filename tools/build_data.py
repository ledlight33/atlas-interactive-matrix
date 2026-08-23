#!/usr/bin/env python3
"""
build_data.py - regenerate the MITRE ATLAS dataset embedded in index.html.

Pulls a pinned MITRE ATLAS release, verifies its SHA-256, transforms the v6
schema (keyed dicts + relationship graph) into the shape the app consumes,
writes a human-readable copy to data/ for auditing, and injects a gzip+base64
payload into index.html between generated markers.

The readable JSON in data/ and the embedded payload are built from the same
parse, and provenance records the source hash, so what ships can always be
checked back against what MITRE published.

Usage:
    python tools/build_data.py                      # build at the pinned version
    python tools/build_data.py --diff-from 2026.03  # build and report what changed
    python tools/build_data.py --print-hash         # fetch and show SHA-256 only
    python tools/build_data.py --no-inject          # regenerate data/ only

Requires: pyyaml
"""

import argparse
import base64
import gzip
import hashlib
import json
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

# --- Pinned release -----------------------------------------------------------
# Bump these together. --print-hash reports the hash of a freshly fetched file.
ATLAS_VERSION = "2026.07"
EXPECTED_SHA256 = "0e07bb07fc6423d72cdf24ddc2038a6905bcbc00ba571064153119ee1a5888d4"

RELEASE_URL = ("https://github.com/mitre-atlas/atlas-data/releases/download/"
               "v{v}/ATLAS-{v}.yaml")
# Historical versions live here; used by --diff-from.
ARCHIVE_URL = ("https://raw.githubusercontent.com/mitre-atlas/atlas-data/"
               "v{pin}/dist/v6/ATLAS-{v}.yaml")

ATLAS_SITE = "https://atlas.mitre.org"

# --- Supersession map ---------------------------------------------------------
# ATLAS retires IDs by deleting them outright - there is no `deprecated` or
# `revoked` field anywhere in the release. Prior casework and published reports
# still cite the old IDs, so we keep an explicit map and resolve them in search.
# Sourced from the v2026.07 release notes and validated against the data at
# build time, so a wrong or stale target fails the build rather than shipping.
SUPERSEDED = {
    "AML.T0019": ("Publish Poisoned Datasets", "AML.T0115.000", "2026.07"),
    "AML.T0058": ("Publish Poisoned Models", "AML.T0115.001", "2026.07"),
    "AML.T0104": ("Publish Poisoned AI Agent Tool", "AML.T0115.002", "2026.07"),
}

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".cache"
DATA = ROOT / "data"
INDEX = ROOT / "index.html"

START = "// <<<ATLAS-DATA-START>>>"
END = "// <<<ATLAS-DATA-END>>>"


def fetch(version, pin=ATLAS_VERSION, archive=False):
    """Download a release YAML, caching it under tools/.cache/."""
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / ("ATLAS-%s.yaml" % version)
    if cached.exists():
        return cached.read_bytes()
    url = (ARCHIVE_URL.format(pin=pin, v=version) if archive
           else RELEASE_URL.format(v=version))
    print("  fetching %s" % url)
    with urllib.request.urlopen(url, timeout=120) as r:
        raw = r.read()
    cached.write_bytes(raw)
    return raw


def absolutise(text):
    """Rewrite ATLAS-relative markdown links to absolute atlas.mitre.org URLs."""
    return re.sub(r"\]\((/(?:techniques|tactics|mitigations|studies)/)",
                  lambda m: "](" + ATLAS_SITE + m.group(1), text)


def transform(doc):
    """Turn the v6 relationship graph into the flat shape the app renders."""
    order = {}
    parent_of = {}
    achieves = defaultdict(list)
    mitigates = defaultdict(list)
    employs = defaultdict(list)

    for _src, rels in doc["relationships"].items():
        for r in rels.get("sequences", []):
            order[r["target"]] = r["position"]
        for r in rels.get("specializes", []):
            parent_of[r["source"]] = r["target"]
        for r in rels.get("achieves", []):
            achieves[r["source"]].append(r["target"])
        for r in rels.get("mitigates", []):
            mitigates[r["source"]].append(r["target"])
        for r in rels.get("employs", []):
            employs[r["source"]].append(r)

    T = doc["techniques"]
    subs_of = defaultdict(list)
    for sub, parent in parent_of.items():
        subs_of[parent].append(sub)

    def tech_record(tid):
        t = T[tid]
        rec = {
            "id": tid,
            "name": t["name"],
            "tactics": sorted(achieves.get(tid, []), key=lambda x: order.get(x, 99)),
            "desc": absolutise(t["description"]),
            "maturity": t["maturity"],
            "platforms": t["platforms"],
        }
        if t.get("attack-reference"):
            rec["attack"] = t["attack-reference"]["id"]
        return rec

    techniques = []
    for tid in T:
        if tid in parent_of:
            continue  # sub-techniques are nested under their parent
        rec = tech_record(tid)
        rec["subs"] = [tech_record(s) for s in sorted(subs_of.get(tid, []))]
        techniques.append(rec)

    tactics = []
    for k, v in sorted(doc["tactics"].items(), key=lambda kv: order.get(kv[0], 99)):
        rec = {"id": k, "name": v["name"], "desc": absolutise(v["description"])}
        if v.get("attack-reference"):
            rec["attack"] = v["attack-reference"]["id"]
        tactics.append(rec)

    mitigations = []
    for k, v in sorted(doc["mitigations"].items()):
        mitigations.append({
            "id": k,
            "name": v["name"],
            "desc": absolutise(v["description"]),
            "categories": v["categories"],
            "lifecycle": v["lifecycle-phases"],
            "techniques": sorted(mitigates.get(k, [])),
        })

    # Validate the supersession map against real data before it can ship.
    live = set(T)
    deprecated = {}
    for old, (name, new, since) in SUPERSEDED.items():
        if old in live:
            raise SystemExit(
                "BUILD FAILED: %s is marked superseded but still exists upstream" % old)
        if new not in live:
            raise SystemExit(
                "BUILD FAILED: %s points at %s, which does not exist upstream" % (old, new))
        deprecated[old] = {"name": name, "supersededBy": new, "since": since}

    # --- Case studies -------------------------------------------------------
    # Each study carries an ordered step list. Step ids are all `S<digits>` and
    # no `leads-to` edge points backwards, so sorting by step id reproduces the
    # topological order exactly; both facts are asserted below rather than
    # assumed, since a future release could break them.
    known_techniques = set(T)
    case_studies = []
    for cid, v in sorted(doc["case-studies"].items()):
        steps = []
        for r in sorted(employs.get(cid, []), key=lambda x: x["step-id"]):
            if not re.fullmatch(r"S\d+", r["step-id"]):
                raise SystemExit(
                    "BUILD FAILED: %s step id %r is not S<digits>; the ordering "
                    "assumption no longer holds." % (cid, r["step-id"]))
            if r["target"] not in known_techniques:
                raise SystemExit(
                    "BUILD FAILED: %s step %s references unknown technique %s"
                    % (cid, r["step-id"], r["target"]))
            nxt = r.get("leads-to") or []
            for n in nxt:
                if n <= r["step-id"]:
                    raise SystemExit(
                        "BUILD FAILED: %s step %s leads back to %s; steps are no "
                        "longer safe to sort by id." % (cid, r["step-id"], n))
            steps.append({
                "id": r["step-id"],
                "tactic": r["tactic"],
                "technique": r["target"],
                "desc": absolutise(r["description"]),
                "next": nxt,
            })

        rec = {
            "id": cid,
            "name": v["name"],
            "desc": absolutise(v["description"]),
            "actor": v["actor"],
            "target": v["target"],
            "date": str(v["date"]),
            # Year / Month / Day - the UI must not print more precision than
            # MITRE actually recorded.
            "granularity": v["date-granularity"],
            "type": v["type"],
            "steps": steps,
            "refs": [{"title": r.get("title", ""), "url": r.get("url", "")}
                     for r in v.get("references", []) if r.get("url")],
        }
        if v.get("reporter"):
            rec["reporter"] = v["reporter"]
        case_studies.append(rec)

    # technique -> case studies that used it, newest first. Sub-technique hits
    # roll up to the parent so selecting T0051 surfaces cases that used
    # T0051.001, which is how an investigator would expect it to behave.
    by_date = {c["id"]: c["date"] for c in case_studies}
    incidents = defaultdict(set)
    for c in case_studies:
        for s in c["steps"]:
            tid = s["technique"]
            incidents[tid].add(c["id"])
            if tid in parent_of:
                incidents[parent_of[tid]].add(c["id"])
    # Sort by (date, id), not date alone: several studies share a date, and a
    # non-total sort over a set lets iteration order - which varies per run under
    # hash randomisation - decide the tie. That would make the build
    # irreproducible and the embedded payload impossible to verify.
    technique_incidents = {
        t: sorted(ids, key=lambda i: (by_date[i], i), reverse=True)
        for t, ids in sorted(incidents.items())
    }

    return {
        "tactics": tactics,
        "techniques": techniques,
        "mitigations": mitigations,
        "deprecated": deprecated,
        "caseStudies": case_studies,
        "techniqueIncidents": technique_incidents,
    }


def summarise(payload):
    return {
        "tactics": len(payload["tactics"]),
        "techniques": len(payload["techniques"]),
        "subtechniques": sum(len(t["subs"]) for t in payload["techniques"]),
        "mitigations": len(payload["mitigations"]),
        "mitigationLinks": sum(len(m["techniques"]) for m in payload["mitigations"]),
        "deprecated": len(payload["deprecated"]),
        "caseStudies": len(payload["caseStudies"]),
        "realIncidents": sum(1 for c in payload["caseStudies"] if c["type"] == "Incident"),
        "caseStudySteps": sum(len(c["steps"]) for c in payload["caseStudies"]),
    }


def flat_ids(payload):
    ids = {}
    for t in payload["techniques"]:
        ids[t["id"]] = t["name"]
        for s in t["subs"]:
            ids[s["id"]] = s["name"]
    return ids


def report_diff(new, old, old_version):
    """Print a human-readable change report between two builds."""
    print("\n=== Changes: %s -> %s ===" % (old_version, ATLAS_VERSION))
    a, b = flat_ids(old), flat_ids(new)

    removed = sorted(set(a) - set(b))
    if removed:
        print("\nREMOVED (%d):" % len(removed))
        for i in removed:
            note = ""
            if i in new["deprecated"]:
                note = "  -> superseded by %s" % new["deprecated"][i]["supersededBy"]
            print("  %s  %s%s" % (i, a[i], note))

    added = sorted(set(b) - set(a))
    if added:
        print("\nADDED (%d):" % len(added))
        for i in added:
            print("  %s  %s" % (i, b[i]))

    renamed = [(i, a[i], b[i]) for i in sorted(set(a) & set(b)) if a[i] != b[i]]
    if renamed:
        print("\nRENAMED (%d):" % len(renamed))
        for i, o, n in renamed:
            print("  %s  %r -> %r" % (i, o, n))

    om = {m["id"]: m for m in old["mitigations"]}
    nm = {m["id"]: m for m in new["mitigations"]}
    new_m = sorted(set(nm) - set(om))
    if new_m:
        print("\nNEW MITIGATIONS (%d):" % len(new_m))
        for i in new_m:
            print("  %s  %s  (%d technique links)" % (i, nm[i]["name"], len(nm[i]["techniques"])))

    mren = [(i, om[i]["name"], nm[i]["name"]) for i in sorted(set(om) & set(nm))
            if om[i]["name"] != nm[i]["name"]]
    if mren:
        print("\nRENAMED MITIGATIONS (%d):" % len(mren))
        for i, o, n in mren:
            print("  %s  %r -> %r" % (i, o, n))

    # Technique -> tactic mapping changes silently move cards on the matrix,
    # so they are called out explicitly rather than left to be noticed.
    at = {t["id"]: set(t["tactics"]) for t in old["techniques"]}
    bt = {t["id"]: set(t["tactics"]) for t in new["techniques"]}
    moved = [(i, at[i], bt[i]) for i in sorted(set(at) & set(bt)) if at[i] != bt[i]]
    if moved:
        print("\nTACTIC MAPPING CHANGES (%d):" % len(moved))
        for i, o, n in moved:
            print("  %s  %s -> %s" % (i, sorted(o), sorted(n)))

    old_links = sum(len(m["techniques"]) for m in old["mitigations"])
    new_links = sum(len(m["techniques"]) for m in new["mitigations"])
    print("\nMitigation coverage: %d links -> %d links (%+d)"
          % (old_links, new_links, new_links - old_links))


def inject(payload, provenance):
    """Replace the generated block in index.html with a fresh payload."""
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    # mtime=0 keeps the build reproducible. Without it gzip stamps the current
    # time into the header and the same input yields a different payload every
    # run, which would make the embedded data impossible to verify against.
    packed = base64.b64encode(gzip.compress(blob.encode("utf-8"), 9, mtime=0)).decode("ascii")

    block = "\n".join([
        START,
        "// Generated by tools/build_data.py from MITRE ATLAS v%s." % provenance["atlasVersion"],
        "// Do not edit by hand - re-run the build script instead.",
        "// Readable source of this payload: data/atlas-%s.json" % provenance["atlasVersion"],
        "const ATLAS_PROVENANCE = %s;" % json.dumps(provenance, indent=2),
        'const ATLAS_PAYLOAD_GZ = "%s";' % packed,
        END,
    ])

    src = INDEX.read_text(encoding="utf-8")
    if START not in src or END not in src:
        raise SystemExit(
            "BUILD FAILED: markers not found in %s. Add %s / %s around the "
            "generated data block." % (INDEX.name, START, END))
    start_i = src.index(START)
    end_i = src.index(END) + len(END)
    INDEX.write_text(src[:start_i] + block + src[end_i:], encoding="utf-8")

    raw_kb = len(blob) / 1024.0
    packed_kb = len(packed) / 1024.0
    print("  embedded %.1f KB base64 (from %.1f KB JSON, %d%% smaller)"
          % (packed_kb, raw_kb, 100 - 100 * packed_kb / raw_kb))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--diff-from", metavar="VERSION",
                    help="also report changes against this earlier ATLAS version")
    ap.add_argument("--print-hash", action="store_true",
                    help="fetch the pinned release and print its SHA-256, then exit")
    ap.add_argument("--no-inject", action="store_true",
                    help="regenerate data/ but leave index.html untouched")
    args = ap.parse_args()

    try:
        import yaml
    except ImportError:
        raise SystemExit("BUILD FAILED: pyyaml is required.  pip install pyyaml")

    print("MITRE ATLAS v%s" % ATLAS_VERSION)
    raw = fetch(ATLAS_VERSION)
    digest = hashlib.sha256(raw).hexdigest()

    if args.print_hash:
        print("  sha256 = %s" % digest)
        return

    if digest != EXPECTED_SHA256:
        raise SystemExit(
            "BUILD FAILED: SHA-256 mismatch - the pinned release does not match "
            "what was published.\n"
            "  expected %s\n"
            "  got      %s\n"
            "Clear tools/.cache/ and retry. If the hash is genuinely new, verify "
            "the release, then update EXPECTED_SHA256." % (EXPECTED_SHA256, digest))
    print("  sha256 verified (%s...)" % digest[:16])

    doc = yaml.safe_load(raw)
    if doc["format-version"] != "6.0.0":
        print("  WARNING: unexpected format-version %s" % doc["format-version"], file=sys.stderr)

    payload = transform(doc)
    counts = summarise(payload)
    provenance = {
        "atlasVersion": ATLAS_VERSION,
        "formatVersion": doc["format-version"],
        "sourceUrl": RELEASE_URL.format(v=ATLAS_VERSION),
        "sha256": digest,
        "atlasModified": str(doc["collection"]["modified-date"]),
        "built": date.today().isoformat(),
        "counts": counts,
    }
    payload["meta"] = provenance

    DATA.mkdir(exist_ok=True)
    readable = DATA / ("atlas-%s.json" % ATLAS_VERSION)
    readable.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (DATA / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    print("  " + "  ".join("%s=%s" % (k, v) for k, v in counts.items()))
    print("  wrote %s (%d KB)" % (readable.relative_to(ROOT), readable.stat().st_size / 1024))

    if not args.no_inject:
        inject(payload, provenance)
        print("  updated %s" % INDEX.name)

    if args.diff_from:
        global SUPERSEDED
        old_doc = yaml.safe_load(fetch(args.diff_from, archive=True))
        # Superseded IDs still exist in older releases, so validation must be
        # skipped while transforming the historical build.
        keep = SUPERSEDED
        SUPERSEDED = {}
        try:
            old_payload = transform(old_doc)
        finally:
            SUPERSEDED = keep
        report_diff(payload, old_payload, args.diff_from)


if __name__ == "__main__":
    main()
