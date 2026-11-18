# LG TV (used as the Mac Studio's monitor)

## The TV

- Model: LG OLED55B4KNA.AKRQLJD (B4, 55"), webOS 24, firmware 23.20.28
- Address: 10.0.10.215 (DHCP; the daemon follows the TV's discovery UUID if it moves)
- Input: HDMI 1 (`com.webos.app.hdmi1`)
- Picture mode in use: `hdrStandard`
- Control ports: 3000 (ws), 3001 (wss, self-signed certificate)

## How the Mac controls it

The av-frameworks daemon (`control-surface-router`) drives TV brightness and volume over
Wi-Fi from the Electra One Mini's knobs.

- Brightness: `picture.backlight` (LG's "OLED Pixel Brightness"), 0–100, with readback.
- Volume: `audio/setVolume` / `audio/getVolume`, used when the Mac's audio output is the LG
  over HDMI.
- It only writes while the LG is the Mac's main display and the TV is on HDMI 1.
- `/api/status` → `router.system.brightness_backend` should say `webos-panel`.

Pairing profile (contains the pairing key and TV certificate, so **keep it private**):
`~/Library/Application Support/AuroraVision/av-frameworks/daemon/lg-tv/brightness.json`

To re-pair, run `~/dev/av-frameworks/control-surface-router/tools/pair-lg-tv.py` with
`bscpylgtv==0.5.5` while the LG is the main display, accept the prompt on the TV, then
restart the daemon.

Full engineering notes: `~/dev/av-frameworks/docs/extended/platform-support.md`
(the "macOS display brightness" and "LG HDMI volume and unexpected dimming" sections).

## Static-image dimming (panel protection), turned OFF on 2026-11-18

The TV kept slowly dimming on static content (the desktop) and then jumping back to
full brightness when the content changed. That behaviour comes from LG's OLED protection:

- **TPC**: Temporal Peak luminance Control
- **GSR**: Global Stress Reduction

Both were turned off on 2026-11-18 over the network with `disable_panel_protection.py`
(in this repo). The TV accepted both commands (`returnValue: True`). The TV has no way to
read these settings back, so the only check is to watch whether a static screen still dims.

**Burn-in risk is accepted.** With these off, static UI at high brightness wears the panel
faster. To reduce the risk:

- Let the TV run its pixel refresh in standby; don't cut power at the wall.
- Use a moving or blank screensaver, and let the Mac turn the display off when idle.

These are hidden service-menu settings. **A firmware update or factory reset can turn them
back on.** If the dimming returns, run the script again:

```sh
uv venv ~/dev/lgtv-control/.venv
uv pip install --python ~/dev/lgtv-control/.venv/bin/python bscpylgtv==0.5.5
~/dev/lgtv-control/.venv/bin/python -I ~/dev/lgtv-control/disable_panel_protection.py
```

The script reuses the daemon's pairing profile and checks the TV model before sending
anything. To turn protection back on, change `False` to `True` in the script.

This change does not cover two things:
- Logo-only dimming is a separate setting: TV Settings → OLED Care → Adjust Logo Brightness.
- The panel's power limit (ABL) still dims large bright areas. That is normal.
- AI Brightness: the firmware refuses reads of `aiPicture.ai_Brightness`, so it is **not
  verified off**. Check it in the TV menu if dimming persists.

Known picture settings (2026-11-05): `backlight` 100, `energySaving` off, `motionEyeCare`
off, `dynamicContrast` off, `hdrDynamicToneMapping` off.

## Troubleshooting

**Knobs do nothing.** Check the daemon status first:

```sh
curl -s http://127.0.0.1:<port>/api/status | python3 -m json.tool | less
```

- `providers[].phase` for `av.control-surface.electra-mini-fw` should not be `unavailable`.
- On 2026-11-18 the Electra failed with `Electra USB write: IOKit 0xe00002ed`
  (`kIOReturnNotResponding`). The TV link was fine; the Mini's firmware had stopped
  responding over USB. Fix: unplug the Mini's USB cable and plug it back in. If that
  doesn't help, restart the daemon.
- If `brightness_backend` is not `webos-panel`, the TV link is down. Check that the TV is
  on, on HDMI 1, and reachable (`nc -z 10.0.10.215 3001`). If needed, re-pair.

**The bscpylgtv script times out on connect.** Its default 2-second connect timeout is too
short for this TV; the script uses `timeout_connect=15`.
