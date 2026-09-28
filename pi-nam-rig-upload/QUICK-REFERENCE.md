# PiPedal quick reference

## Hotspot (phone → Pi, no router)

| | |
|---|---|
| Password | *redacted — see `secrets.local.md` (not committed; copy from `secrets.example.md`)* |
| Network name (SSID) | **pipedal** |
| Channel | 6 (2.4 GHz). If it drops out at a venue, try 1 or 11 |
| Trigger | No ethernet connection (hotspot turns on when the Ethernet cable is unplugged) |
| UI address | `http://pipedal.local`, or fall back to `http://172.23.0.2` |

While the hotspot is on, the Pi can't join normal Wi-Fi. Plug Ethernet back in to recover access.

**Status (2026-09-23): hotspot comes up and devices can join it, but the UI didn't load yet on a
laptop.** Unfinished troubleshooting, do this next:

1. On the device joined to `pipedal`, run `ipconfig` (Windows) and look at the Wi-Fi section.
   - **Default Gateway** = the Pi's real hotspot address. Browse to `http://<that address>`.
     `172.23.0.2` above is from old notes, not confirmed on this Pi.
   - **IPv4 Address starting 169.254** = the device never got an address from the Pi, so the
     problem is on the Pi's hotspot side (check `journalctl -u pipedald` over Ethernet).
2. Type `http://` explicitly (browsers auto-switch to https). `pipedal.local` often fails on
   Windows; use the IP. "No internet" on this network is normal. Turn off any VPN.
3. Try a phone too. Phone works but laptop doesn't = a laptop setting, not the Pi.

Windows asks for a "PIN from the router label" when joining. That's WPS; click **"Connect using
a security key instead"** and enter the password.

When testing, pull **only** the Ethernet cable. Hold the Pico's USB lead. Knocking it out
reboots the Pico and blanks the OLED until the relay resends (about 10 s now).

Old home Wi-Fi networks were saved on the Pi (`Wi-Fi CA90EC 2.4G/5G`,
`netplan-wlan0-TelstraA9DD42`). Delete commands, if not already done:
`sudo nmcli connection delete "<name>"`. Never delete `netplan-eth0` (that's Ethernet).

## At home

- **Home Wi-Fi (current, 2026-09-24):** `ssh jesse@192.168.0.73`, UI `http://192.168.0.73/`
- Ethernet (earlier network): was `192.168.20.32`
- Hostname `pipedal` (`http://pipedal.local`). IPs can change; check the router's device list
  if it stops answering.

## Footswitch OLED relay

- Live log: `journalctl -u pipedal-tuner-relay -f`
- Restart: `sudo systemctl restart pipedal-tuner-relay`
- Code on the Pi: `~/pico-footswitch-v2/`
