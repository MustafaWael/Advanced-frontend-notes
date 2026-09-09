#!/usr/bin/env python3
"""Vault status audit — the numbers the Base views and the Quiz Queue depend on.

Run from anywhere:  python3 "98 - Vault Operations/Scripts/status-audit.py"
Reads only; writes nothing. Excludes 98 - Vault Operations, MOCs and Checklists,
matching the Base.base filters.
"""
import datetime, pathlib, re, sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
STATUSES = ["not-started", "learning", "solid"]
PRIORITIES = ["must-know", "important", "deep-dive"]
STALE_DAYS = 90
TODAY = datetime.date.today()

def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            out[km.group(1)] = km.group(2).strip().strip('"').strip("'")
    return out

notes = []
for p in sorted(ROOT.rglob("*.md")):
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith(("98 - Vault Operations", ".")) or "/.git/" in rel:
        continue
    if "MOC" in p.name or "Checklist" in p.name:
        continue
    fm = frontmatter(p.read_text(encoding="utf-8", errors="replace"))
    if "status" not in fm:
        continue
    notes.append((rel, fm))

by_status = Counter(fm.get("status", "?") for _, fm in notes)
grid = defaultdict(Counter)
for _, fm in notes:
    grid[fm.get("status", "?")][fm.get("priority", "?")] += 1

print(f"\nVAULT STATUS AUDIT — {TODAY}   ({len(notes)} drillable notes)\n")
w = max(len(s) for s in list(by_status) + STATUSES + ["status"]) + 2
print("  " + "status".ljust(w) + "".join(p.rjust(12) for p in PRIORITIES) + "total".rjust(9))
print("  " + "-" * (w + 45))
for s in STATUSES + [k for k in by_status if k not in STATUSES]:
    row = grid[s]
    print("  " + s.ljust(w) + "".join(str(row[p]).rjust(12) for p in PRIORITIES)
          + str(by_status[s]).rjust(9))

tier1 = grid["learning"]["must-know"]
tier2 = grid["learning"]["important"]
tier3 = grid["not-started"]["must-know"]
print(f"\n  Quiz Queue  Tier 1 (learning+must-know): {tier1}"
      f"   Tier 2 (learning+important): {tier2}"
      f"   Tier 3 (not-started+must-know): {tier3}")

print("\nFLAGS")
if by_status["learning"] == 0:
    print("  ! Nothing is `learning`. Base 'Quiz Pool' and 'Study Queue' render EMPTY,")
    print("    and Quiz Queue Tiers 1-2 are empty by construction. Flip notes to")
    print("    `learning` when you start them or the status-driven tooling is inert.")
elif tier1 > 10:
    print(f"  ! Tier 1 is {tier1} notes (>10). Per the Quiz Queue: the statuses are")
    print("    stale, not the plan ambitious. Reconcile before scheduling.")
else:
    print(f"  ok Tier 1 pool is {tier1} notes — a workable week.")

stale = []
for rel, fm in notes:
    v = fm.get("verified_on")
    if not v:
        continue
    try:
        d = datetime.date.fromisoformat(v)
    except ValueError:
        print(f"  ! unparseable verified_on ({v}): {rel}")
        continue
    if (TODAY - d).days > STALE_DAYS:
        stale.append(((TODAY - d).days, rel, fm.get("version_scope", "")))
if stale:
    print(f"\n  ! {len(stale)} version-sensitive notes unverified for >{STALE_DAYS} days:")
    for days, rel, scope in sorted(stale, reverse=True)[:15]:
        print(f"      {days:>4}d  {rel}" + (f"   [{scope}]" if scope else ""))

missing = [rel for rel, fm in notes
           if fm.get("priority") not in PRIORITIES or fm.get("status") not in STATUSES
           or "module" not in fm]
if missing:
    print(f"\n  ! {len(missing)} notes with malformed frontmatter (invisible to Base views):")
    for rel in missing[:15]:
        print(f"      {rel}")

print("\nBY MODULE (not-started / learning / solid)")
mods = defaultdict(Counter)
for rel, fm in notes:
    mods[rel.split("/")[0]][fm.get("status", "?")] += 1
for mod in sorted(mods):
    c = mods[mod]
    done = c["solid"]
    total = sum(c.values())
    bar = "#" * round(20 * done / total) if total else ""
    print(f"  {mod[:44]:<46} {c['not-started']:>4} / {c['learning']:>3} / {c['solid']:>3}  {bar}")
print()
