#!/usr/bin/env python3
"""
Move one snapshot to another slot of the same preset in the LIVE bank, and
optionally rename it. Changes nothing else.

    move-snapshot.py "9 Test" 1 6 Fascination [--dry-run]

Slots are 1-6 as shown in PiPedal. The destination must be empty; the source
slot is left empty. selectedSnapshot follows the moved snapshot if it was the
selected one. Run with pipedald STOPPED, as for the other bank scripts:
    sudo systemctl stop pipedald
    sudo python3 move-snapshot.py "9 Test" 1 6 Fascination
    sudo systemctl start pipedald
"""

import datetime
import json
import os
import shutil
import sys

BANK = "/var/pipedal/presets/Default+Bank.bank"


def backup_dir():
    user = os.environ.get("SUDO_USER")
    if user:
        import pwd
        return pwd.getpwnam(user).pw_dir
    return os.path.expanduser("~")


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv[1:]
    if len(args) not in (3, 4):
        sys.exit(__doc__)
    name, src, dst = args[0], int(args[1]) - 1, int(args[2]) - 1
    new_name = args[3] if len(args) == 4 else None
    bank_path = os.environ.get("BANK_PATH", BANK)

    with open(bank_path) as f:
        bank = json.load(f)
    st = os.stat(bank_path)

    matches = [e["preset"] for e in bank["presets"] if e["preset"]["name"] == name]
    if len(matches) != 1:
        sys.exit("expected exactly one preset named %r, found %d" % (name, len(matches)))
    preset = matches[0]
    snaps = preset["snapshots"]
    if not (0 <= src < 6 and 0 <= dst < 6):
        sys.exit("slots must be 1-6")
    if snaps[src] is None:
        sys.exit("slot %d is empty" % (src + 1))
    if snaps[dst] is not None:
        sys.exit("slot %d already holds %r" % (dst + 1, snaps[dst]["name"]))

    snap = snaps[src]
    old_name = snap["name"]
    if new_name:
        snap["name"] = new_name
    snaps[dst], snaps[src] = snap, None
    if preset.get("selectedSnapshot") == src:
        preset["selectedSnapshot"] = dst

    print("%s: slot %d %r -> slot %d %r" % (name, src + 1, old_name, dst + 1, snap["name"]))
    print("  now:", [s["name"] if s else None for s in snaps],
          "selected slot", preset["selectedSnapshot"] + 1)

    if dry_run:
        print("--dry-run: nothing written.")
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(backup_dir(), "bank-backup-" + stamp + ".json")
    shutil.copy2(bank_path, backup)
    if os.environ.get("SUDO_UID"):
        os.chown(backup, int(os.environ["SUDO_UID"]), int(os.environ.get("SUDO_GID", -1)))
    print("backup written to", backup)

    tmp = bank_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(bank, f, indent=1)
    json.load(open(tmp))
    os.replace(tmp, bank_path)
    os.chown(bank_path, st.st_uid, st.st_gid)
    os.chmod(bank_path, st.st_mode)
    print("done.")


if __name__ == "__main__":
    main()
