#!/usr/bin/env python3
"""
Give every snapshot a stored value for every plugin in its preset, in place.

A snapshot value missing for a plugin means "leave that plugin as it is" when
the snapshot is recalled -- so the plugin stops following snapshot changes (a
pedal switched on in one snapshot is not switched off again in the next). This
adds the missing values and changes nothing else.

Where each missing value comes from:
  1. --from BACKUP.json: the same plugin's value in the same-named snapshot of
     that bank backup (exact, as PiPedal wrote it), if it has one;
  2. otherwise the plugin's own current values in the preset.

    python3 fill-missing-snapshot-values.py --dry-run [--from bank-backup-X.json]
    sudo systemctl stop pipedald
    sudo python3 fill-missing-snapshot-values.py [--from bank-backup-X.json]
    sudo systemctl start pipedald

Backs up the bank first and checks the result, like add-menu-plugins-to-bank.py.
Idempotent: a bank with nothing missing is left untouched.
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


def backup_values(path):
    """{(preset name, snapshot name, instanceId): value} from a bank file."""
    out = {}
    for entry in json.load(open(path))["presets"]:
        preset = entry["preset"]
        for snap in preset["snapshots"]:
            if snap:
                for value in snap["values"]:
                    out[(preset["name"], snap["name"], value["instanceId"])] = value
    return out


def fill(bank, backup):
    """Mutates `bank`. Returns a list of (preset, snapshot, plugin, source)."""
    filled = []
    for entry in bank["presets"]:
        preset = entry["preset"]
        flat = kraken.flatten(preset["items"])
        order = {it["instanceId"]: n for n, it in enumerate(flat)}
        for snap in preset["snapshots"]:
            if not snap:
                continue
            have = {v["instanceId"] for v in snap["values"]}
            for it in flat:
                if it["instanceId"] in have:
                    continue
                old = backup.get((preset["name"], snap["name"], it["instanceId"]))
                snap["values"].append(json.loads(json.dumps(old)) if old else kraken.snap_value(it))
                filled.append((preset["name"], snap["name"], it["pluginName"],
                               "backup" if old else "the plugin's current values"))
            snap["values"].sort(key=lambda v: order.get(v["instanceId"], len(order)))
    return filled


def verify(bank):
    for entry in bank["presets"]:
        preset = entry["preset"]
        ids = sorted(it["instanceId"] for it in kraken.flatten(preset["items"]))
        for snap in preset["snapshots"]:
            if snap and sorted(v["instanceId"] for v in snap["values"]) != ids:
                sys.exit("%s / %s: snapshot values still don't match the chain" % (preset["name"], snap["name"]))


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    backup = backup_values(args[args.index("--from") + 1]) if "--from" in args else {}
    bank_path = os.environ.get("BANK_PATH", kraken.BANK)

    with open(bank_path) as f:
        bank = json.load(f)
    st = os.stat(bank_path)

    filled = fill(bank, backup)
    for preset, snap, plugin, source in filled:
        print("%-26s %-14s + %-28s from %s" % (preset, snap, plugin, source))
    verify(bank)

    if dry_run or not filled:
        print("\n%s: nothing written." % ("--dry-run" if dry_run else "Nothing was missing"))
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(kraken.backup_dir(), "bank-backup-" + stamp + ".json")
    shutil.copy2(bank_path, backup_path)
    if os.environ.get("SUDO_UID"):
        os.chown(backup_path, int(os.environ["SUDO_UID"]), int(os.environ.get("SUDO_GID", -1)))
    print("\nbackup written to", backup_path)

    tmp = bank_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(bank, f, indent=1)
    json.load(open(tmp))                       # parse-check before swapping in
    os.replace(tmp, bank_path)
    os.chown(bank_path, st.st_uid, st.st_gid)
    os.chmod(bank_path, st.st_mode)
    print("filled %d missing snapshot value(s)." % len(filled))


if __name__ == "__main__":
    main()
