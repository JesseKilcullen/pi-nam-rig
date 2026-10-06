#!/usr/bin/env python3
"""
Append "9 Test" to the LIVE bank, in place -- and change nothing else.

An experiment preset modelled on "6 Massive": two amp chains in parallel (a
Kraken on top behind a gain pedal, a clean Tweed underneath), the settings
menu's Pitch Shift and Graphic EQ, and every effect in the bank: chorus,
tremolo, delay and reverb.

Additive like add-menu-plugins-to-bank.py, NOT a regenerate: the live bank has
by-ear edits the generator doesn't, and a regenerate would overwrite them.
Idempotent: skipped if "9 Test" already exists.

Run with pipedald STOPPED (it rewrites the bank from memory otherwise):
    python3 add-test-preset.py --dry-run     # read-only, safe anytime
    sudo systemctl stop pipedald
    sudo python3 add-test-preset.py
    sudo systemctl start pipedald
Rollback: copy the printed backup over the bank (see pipedal-presets-howto.md).

The definition itself (chain, snapshots) is in add-muse-opeth-presets.py --
this script only appends it to a bank that doesn't have it yet. A bank that
already has "9 Test" is left alone.
"""

import datetime
import importlib.util
import json
import os
import shutil
import sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "kraken", os.path.join(here, "build-kraken-presets.py"))
kraken = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kraken)

# The preset's definition lives in add-muse-opeth-presets.py, next to the
# other extras, so the generator and this script can't drift apart.
spec2 = importlib.util.spec_from_file_location(
    "extras", os.path.join(here, "add-muse-opeth-presets.py"))
extras = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(extras)

NAME = "9 Test"


def items():
    return kraken.with_menu_plugins(extras._test_items())


def snapshots(its):
    return extras.snapshots_for(NAME, its)


def build(bank):
    its = items()
    flat = kraken.flatten(its)
    ids = [it["instanceId"] for it in flat]
    entry_id = max([e["instanceId"] for e in bank["presets"]] + [0]) + 1
    return {
        "instanceId": entry_id,
        "preset": {
            "name": NAME,
            "input_volume_db": 0,
            "output_volume_db": 0,
            "items": its,
            "nextInstanceId": max(ids) + 1,
            "snapshots": snapshots(its),
            "selectedSnapshot": 0,
            "selectedPlugin": [i["instanceId"] for i in flat
                               if i["uri"].endswith("toob-nam")][-1],
        },
    }


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    bank_path = os.environ.get("BANK_PATH", kraken.BANK)
    if not os.path.exists(bank_path):
        sys.exit("bank not found: " + bank_path)
    with open(bank_path) as f:
        bank = json.load(f)
    st = os.stat(bank_path)

    if any(e["preset"]["name"] == NAME for e in bank["presets"]):
        print("%s already in the bank -- nothing to do." % NAME)
        return

    entry = build(bank)
    kraken.preflight([entry])
    kraken.check_ranges([entry])
    kraken.report([entry])

    for snap in entry["preset"]["snapshots"]:
        if snap and len(snap["values"]) != len(kraken.flatten(entry["preset"]["items"])):
            sys.exit("snapshot %s is missing item values" % snap["name"])

    if dry_run:
        print("\n--dry-run: nothing written.")
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(kraken.backup_dir(), "bank-backup-" + stamp + ".json")
    shutil.copy2(bank_path, backup)
    if os.environ.get("SUDO_UID"):
        os.chown(backup, int(os.environ["SUDO_UID"]),
                 int(os.environ.get("SUDO_GID", -1)))
    print("\nbackup written to", backup)

    bank["presets"].append(entry)
    bank["nextInstanceId"] = max(bank.get("nextInstanceId", 0),
                                 entry["instanceId"] + 1)

    tmp = bank_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(bank, f, indent=1)
    json.load(open(tmp))                       # parse-check before swapping in
    os.replace(tmp, bank_path)
    os.chown(bank_path, st.st_uid, st.st_gid)
    os.chmod(bank_path, st.st_mode)
    print("added %s." % NAME)


if __name__ == "__main__":
    main()
