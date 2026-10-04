#!/usr/bin/env python3
"""
Read-only: build every preset in memory with the generator scripts and compare
against the live bank, to show exactly what a regenerate would change.

    python3 check-bank-diff.py [--ignore-plugin SUBSTRING ...]

Instance ids are ignored (the generator renumbers them). Plugins matching an
--ignore-plugin substring are dropped from the generated side before comparing,
so with --ignore-plugin graphiceq --ignore-plugin pitch-shift this answers
"is a regenerate identical to the live bank apart from those two plugins?".
Anything else it prints is a live edit a regenerate would overwrite.

Writes nothing and needs no sudo or service stop.
"""

import importlib.util
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("muse", os.path.join(here, "add-muse-opeth-presets.py"))
muse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(muse)
kraken = muse.kraken

ignore = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--ignore-plugin"]


def keep(it):
    return not any(sub in it["uri"] for sub in ignore)


def norm(obj):
    """Drop instance ids anywhere, so structure and values are what's compared.
    PiPedal re-orders controlValues and adds float noise (0.4 -> 0.400000006),
    so those compare as {key: value rounded to 4 places}."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ("instanceId", "nextInstanceId", "selectedPlugin"):
                continue
            if k == "controlValues" and isinstance(v, list):
                out[k] = {c["key"]: round(float(c["value"]), 4) for c in v}
            else:
                out[k] = norm(v)
        return out
    if isinstance(obj, list):
        return [norm(v) for v in obj]
    return obj


def prune(items):
    out = []
    for it in items:
        if not keep(it):
            continue
        it = dict(it)
        for key in ("topChain", "bottomChain"):
            if isinstance(it.get(key), dict):
                chain = dict(it[key])
                chain["items"] = prune(chain.get("items") or [])
                it[key] = chain
        out.append(it)
    return out


def generated():
    result = []
    for name, items, *rest in kraken.presets():
        items = kraken.with_menu_plugins(items)
        result.append({
            "name": name,
            "output_volume_db": rest[0] if rest else 0,
            "items": items,
            "snapshots": kraken.snapshots_for(name, items),
        })
    return result


def drop_snapshot_values(snapshots, dropped_ids):
    out = []
    for snap in snapshots:
        if snap is None:
            out.append(None)
            continue
        snap = dict(snap)
        snap["values"] = [v for v in snap["values"] if v["instanceId"] not in dropped_ids]
        out.append(snap)
    return out


def diff(a, b, path=""):
    if type(a) != type(b):
        yield "%s: %r != %r" % (path, a, b)
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                yield "%s/%s: only in live bank" % (path, k)
            elif k not in b:
                yield "%s/%s: only in generated" % (path, k)
            else:
                yield from diff(a[k], b[k], "%s/%s" % (path, k))
    elif isinstance(a, list):
        if len(a) != len(b):
            yield "%s: length %d != %d" % (path, len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            yield from diff(x, y, "%s[%d]" % (path, i))
    elif a != b:
        yield "%s: %r != %r" % (path, a, b)


bank = json.load(open(kraken.BANK))
live = {e["preset"]["name"]: e["preset"] for e in bank["presets"]}

problems = 0
for gen in generated():
    name = gen["name"]
    if name not in live:
        print("%-26s not in the live bank" % name)
        problems += 1
        continue
    dropped = {it["instanceId"] for it in kraken.flatten(gen["items"]) if not keep(it)}
    gen_items = prune(gen["items"])
    gen_snaps = drop_snapshot_values(gen["snapshots"], dropped)

    live_p = live[name]
    left = {"items": norm(live_p["items"]), "snapshots": norm(live_p["snapshots"]),
            "output_volume_db": live_p["output_volume_db"]}
    right = {"items": norm(gen_items), "snapshots": norm(gen_snaps),
             "output_volume_db": gen["output_volume_db"]}
    lines = list(diff(left, right))
    if lines:
        problems += 1
        print("%-26s %d difference(s) vs live bank:" % (name, len(lines)))
        for line in lines[:12]:
            print("    " + line[:160])
        if len(lines) > 12:
            print("    ... %d more" % (len(lines) - 12))
    else:
        print("%-26s identical to the live bank%s" % (name, " (ignoring %s)" % ", ".join(ignore) if ignore else ""))

sys.exit(1 if problems else 0)
