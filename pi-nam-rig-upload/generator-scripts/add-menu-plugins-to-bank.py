#!/usr/bin/env python3
"""
Add the settings menu's two plugins (Pitch Shift and Graphic EQ) to every
preset in the LIVE bank, in place -- and change nothing else.

Why not just regenerate with build-kraken-presets.py? Because the live bank has
by-ear edits made in the PiPedal UI that the generator doesn't have (see
check-bank-diff.py), and a regenerate would silently overwrite them. This
script is additive: it inserts the two items into each preset's chain and a
matching value into every snapshot, and leaves every existing value alone.

Where they go (same rule as build-kraken-presets.py's with_menu_plugins):
  Pitch Shift  in front of the first amp/pedal capture or Split
  Graphic EQ   right after the preset's main 3-band/parametric EQ, before the
               chorus/delay/reverb (a mono plugin after a stereo one would
               lose the right channel)

Idempotent: a preset that already has both is skipped.

Run with pipedald STOPPED (it rewrites the bank from memory otherwise):
    python3 add-menu-plugins-to-bank.py --dry-run     # read-only, safe anytime
    sudo systemctl stop pipedald
    sudo python3 add-menu-plugins-to-bank.py
    sudo systemctl start pipedald
Rollback: copy the printed backup over the bank (see pipedal-presets-howto.md).
"""

import datetime
import importlib.util
import json
import os
import shutil
import sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("kraken", os.path.join(here, "build-kraken-presets.py"))
kraken = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kraken)

GEQ_URI = kraken.P + "toob-graphiceq"
NEW_URIS = (kraken.PITCH_URI, GEQ_URI)


def add_to_preset(preset):
    """Mutates `preset`. Returns the names of the plugins added ([] if skipped)."""
    flat = kraken.flatten(preset["items"])
    have = {it["uri"] for it in flat}
    present = [u for u in NEW_URIS if u in have]
    if len(present) == len(NEW_URIS):
        return []
    if present:
        sys.exit("%s already has %s but not the other -- fix by hand first."
                 % (preset["name"], present))

    old_ids = {it["instanceId"] for it in flat}
    new_items = kraken.with_menu_plugins(preset["items"])

    next_id = max(preset.get("nextInstanceId", 0), max(old_ids) + 1)
    added = []
    for it in kraken.flatten(new_items):
        if it["uri"] in NEW_URIS and it["uri"] not in have:
            it["instanceId"] = next_id          # the generator's counter could collide
            next_id += 1
            added.append(it)
    preset["items"] = new_items
    preset["nextInstanceId"] = next_id

    order = {it["instanceId"]: n for n, it in enumerate(kraken.flatten(new_items))}
    for snap in preset["snapshots"]:
        if not snap:
            continue
        snap["values"] += [kraken.snap_value(it) for it in added]
        snap["values"].sort(key=lambda v: order.get(v["instanceId"], len(order)))
    return [it["pluginName"] for it in added]


def verify(bank):
    """Our two plugins must be in every snapshot, with unique ids. Gaps that
    were ALREADY in the bank (e.g. a plugin added in the UI after the
    snapshots were made) are reported but left alone -- fixing someone's
    snapshots silently is not this script's job."""
    for entry in bank["presets"]:
        preset = entry["preset"]
        flat = kraken.flatten(preset["items"])
        ids = [it["instanceId"] for it in flat]
        if len(ids) != len(set(ids)):
            sys.exit("%s: duplicate instance ids" % preset["name"])
        ours = {it["instanceId"] for it in flat if it["uri"] in NEW_URIS}
        for snap in preset["snapshots"]:
            if not snap:
                continue
            have = {v["instanceId"] for v in snap["values"]}
            if not ours <= have:
                sys.exit("%s / %s: missing a value for the new plugins"
                         % (preset["name"], snap["name"]))
            gaps = [it["pluginName"] for it in flat
                    if it["instanceId"] not in have]
            if gaps:
                print("  note: %s / %s has no value for %s (already so before this script; left as is)"
                      % (preset["name"], snap["name"], ", ".join(gaps)))


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    bank_path = os.environ.get("BANK_PATH", kraken.BANK)   # override for testing on a copy
    if not os.path.exists(bank_path):
        sys.exit("bank not found: " + bank_path)

    with open(bank_path) as f:
        bank = json.load(f)
    st = os.stat(bank_path)

    changed = 0
    for entry in bank["presets"]:
        preset = entry["preset"]
        added = add_to_preset(preset)
        chain = " > ".join(kraken.short_name(it["uri"]).replace("toob-", "")
                           for it in preset["items"])
        if added:
            changed += 1
            print("%-26s + %s\n    %s" % (preset["name"], ", ".join(added), chain))
        else:
            print("%-26s already has both -- skipped" % preset["name"])
    verify(bank)

    if dry_run or not changed:
        print("\n%s: nothing written." % ("--dry-run" if dry_run else "No changes needed"))
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(kraken.backup_dir(), "bank-backup-" + stamp + ".json")
    shutil.copy2(bank_path, backup)
    if os.environ.get("SUDO_UID"):
        os.chown(backup, int(os.environ["SUDO_UID"]), int(os.environ.get("SUDO_GID", -1)))
    print("\nbackup written to", backup)

    tmp = bank_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(bank, f, indent=1)
    json.load(open(tmp))                       # parse-check before swapping in
    os.replace(tmp, bank_path)
    os.chown(bank_path, st.st_uid, st.st_gid)
    os.chmod(bank_path, st.st_mode)
    print("wrote %d preset(s) with the menu plugins." % changed)


if __name__ == "__main__":
    main()
