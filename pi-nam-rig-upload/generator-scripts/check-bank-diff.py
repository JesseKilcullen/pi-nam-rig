#!/usr/bin/env python3
"""
Read-only: build every preset in memory with the generator scripts and compare
it with the live bank, to show exactly what a regenerate would change.

    python3 check-bank-diff.py

"No differences" means a regenerate would reproduce the live bank (apart from the
notes below). Anything listed is something in the live bank -- usually a by-ear edit
made in the PiPedal UI -- that a regenerate would overwrite: fold it into the
generator first.

What is compared: the output volume, which plugins each preset has and in what
order, and every snapshot's name, colour and per-plugin values (on/off, controls,
file paths). Plugins are matched by (name, nth of that name), not instance id.

What is deliberately NOT compared: the preset-level plugin values. PiPedal keeps
the *selected snapshot's* values there, so they differ from the generator's
"home" values whenever the bank was saved on another snapshot -- that is noise.

A snapshot with no stored value for a plugin (e.g. a plugin added in the UI
after the snapshots were made) is reported as a note, not a difference: the
generator stores a value for every plugin in every snapshot.

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

AUDIO_ROOT = "/var/pipedal/audio_uploads/"


def keyed(items):
    """Plugins as {(short name, nth of that name): item}, Split children included."""
    seen, out = {}, {}
    for it in kraken.flatten(items):
        short = kraken.short_name(it["uri"])
        nth = seen.get(short, 0)
        seen[short] = nth + 1
        out[(short, nth)] = it
    return out


def controls(holder):
    return {c["key"]: c["value"] for c in holder["controlValues"]}


def paths(holder):
    out = {}
    for prop, raw in holder["pathProperties"].items():
        value = json.loads(raw)["value"]
        out[prop.rsplit("/", 1)[-1]] = value[len(AUDIO_ROOT):] if value.startswith(AUDIO_ROOT) else value
    return out


def same(a, b):
    try:
        return abs(float(a) - float(b)) < 1e-3
    except (TypeError, ValueError):
        return a == b


def compare_preset(name, items, output_volume_db, snapshots, live):
    """Returns (differences, notes) as lists of strings."""
    diffs, notes = [], []
    if live["output_volume_db"] != output_volume_db:
        diffs.append("output volume: generator %s, live %s" % (output_volume_db, live["output_volume_db"]))

    gen_items, live_items = keyed(items), keyed(live["items"])
    for key in sorted(set(live_items) - set(gen_items)):
        diffs.append("plugin %s is in the live bank only" % (key,))
    for key in sorted(set(gen_items) - set(live_items)):
        diffs.append("plugin %s is in the generator only" % (key,))
    gen_order = [k for k in (kraken.short_name(i["uri"]) for i in kraken.flatten(items))]
    live_order = [k for k in (kraken.short_name(i["uri"]) for i in kraken.flatten(live["items"]))]
    if not diffs and gen_order != live_order:
        diffs.append("plugin order: generator %s, live %s" % (gen_order, live_order))

    gen_by_id = {it["instanceId"]: key for key, it in gen_items.items()}
    live_by_id = {it["instanceId"]: key for key, it in live_items.items()}

    for gs, ls in zip(snapshots, live["snapshots"]):
        if gs is None and ls is None:
            continue
        if (gs is None) != (ls is None):
            diffs.append("a snapshot slot is empty on one side only")
            continue
        label = "snapshot %r" % gs["name"]
        if (gs["name"], gs.get("color")) != (ls["name"], ls.get("color")):
            diffs.append("%s: name/colour generator %r/%r, live %r/%r"
                         % (label, gs["name"], gs.get("color"), ls["name"], ls.get("color")))
        gvals = {gen_by_id[v["instanceId"]]: v for v in gs["values"]}
        lvals = {live_by_id[v["instanceId"]]: v for v in ls["values"] if v["instanceId"] in live_by_id}
        for key in sorted(set(gvals) & set(lvals)):
            g, l = gvals[key], lvals[key]
            if g["isEnabled"] != l["isEnabled"]:
                diffs.append("%s: %s enabled generator %s, live %s" % (label, key, g["isEnabled"], l["isEnabled"]))
            gc, lc = controls(g), controls(l)
            for control in sorted(set(gc) | set(lc)):
                if control not in gc or control not in lc:
                    diffs.append("%s: %s control %r is on one side only" % (label, key, control))
                elif not same(gc[control], lc[control]):
                    diffs.append("%s: %s %s generator %s, live %s" % (label, key, control, gc[control], lc[control]))
            gp, lp = paths(g), paths(l)
            for prop in sorted(set(gp) | set(lp)):
                if gp.get(prop) != lp.get(prop):
                    diffs.append("%s: %s %s generator %r, live %r" % (label, key, prop, gp.get(prop), lp.get(prop)))
        for key in sorted(set(gvals) - set(lvals)):
            notes.append("%s has no stored value for %s (the generator stores one)" % (label, key))
    return diffs, notes


def main():
    live = {e["preset"]["name"]: e["preset"]
            for e in json.load(open(os.environ.get("BANK_PATH", kraken.BANK)))["presets"]}
    problems = 0
    for name, items, *rest in kraken.presets():
        items = kraken.with_menu_plugins(items)
        diffs, notes = compare_preset(name, items, rest[0] if rest else 0,
                                      kraken.snapshots_for(name, items), live[name])
        status = "identical" if not diffs else "%d difference(s)" % len(diffs)
        print("%-26s %s" % (name, status))
        for line in diffs:
            print("    " + line[:170])
        for line in notes:
            print("    note: " + line[:170])
        problems += bool(diffs)
    missing = sorted(set(live) - {n for n, *_ in kraken.presets()})
    for name in missing:
        print("%-26s is in the live bank only" % name)
        problems += 1
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
