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

## Signal format: 4K 120 Hz VRR, YCbCr 4:4:4, 10-bit, HDR10 (set up 2026-11-16)

Target and current signal: **3840×2160 @ 120 Hz, VRR (40–120 Hz), YCbCr 4:4:4, 10-bit, HDR10**.

Starting point (TV signal overlay): `YCBCR420 8b 4L12 SDR 120Hz VRR 3840x2160p@120`, which
meant 4:2:0 chroma, 8-bit and SDR. (`4L12` is HDMI 2.1 FRL, 4 lanes at 12 Gbps.)

What changed:
1. **Mac:** System Settings → Displays → LG TV SSCR2: **High Dynamic Range on**, refresh rate
   **Variable (40–120 Hz)**, resolution 3840×2160. Use the LG display colour profile and keep
   Night Shift off. The 4 Nov session had set a fixed 120 Hz; on 16 Nov this was changed to
   variable.
2. **TV** (done by hand, for the Mac's HDMI input): Settings → General → External Devices →
   HDMI Settings:
   - **4:4:4 Pass Through: On**
   - **HDMI Deep Colour: 4K** (`uhdDeepColorHDMI1` was also turned on over the network on 4 Nov)

Result (TV signal overlay): `YCBCR444 10b 4L12 HDR10`, at 120 Hz with VRR.

**To check the signal:** press the **green button** on the LG remote repeatedly until the
signal overlay appears.

**RGB instead of YCbCr:** macOS picks YCbCr itself. RGB would need BetterDisplay's
Color Mode setting. This was tried and dropped on 2026-11-16 (BetterDisplay was installed
and then uninstalled, with nothing changed). YCbCr 4:4:4 10-bit already keeps full chroma
resolution, so RGB is not expected to look noticeably different.

4:4:4 Pass Through can't be set over the network on this firmware. The API refuses the key
`444BypassHDMI1` ("Some keys are not allowed for the request"), so set it in the TV menu.

## Picture settings for monitor use (set up 2026-11-04)

Goal: accurate colour, brightness and HDR for desktop use, with as little processing as
possible. Most of this was done over the network with `bscpylgtv` (`settings/setSystemSettings`)
and read back afterwards. Snapshots are in `snapshots/`:
- `before-monitor-setup.json`: the original state (HDR Game preset, Adobe RGB gamut,
  colour temperature 0, Deep Colour off)
- `hdr-standard-before.json`: the HDR Standard preset before it was corrected
- `monitor-setup-readback.json`: the final readback

**Input:**
- HDMI 1 is set to **PC** mode (input icon "PC", label "Mac Studio"), using
  `set_device_info('HDMI_1', 'pc', 'Mac Studio')`. PC mode turns off most video processing.
- HDMI Deep Colour on (see the signal section above)
- Just Scan **on** (1:1 pixel mapping, no overscan); aspect ratio 16:9

**Picture.** These values were applied to both HDR Game and HDR Standard. Changing the
refresh rate switched the TV from HDR Game to HDR Standard, and each preset keeps its own
values.

| Setting | Value | Why |
|---|---|---|
| Picture mode | `hdrStandard` (active; `hdrGame` also set up) | follows the HDR signal |
| OLED Pixel Brightness (`backlight`) | set by the Electra knob (was 58, then 64) | 100 gives full HDR headroom |
| Contrast / Brightness | 100 / 50 | reference values |
| Colour / Tint | 50 / 0 | neutral |
| Sharpness | 0 | no edge enhancement |
| Colour temperature | −50 (= Warm 50) | closest to D65 |
| Colour gamut | auto | follows the signal (Rec.709 / BT.2020); not Adobe RGB |
| Black level | auto | |
| Dynamic Tone Mapping | off | no content-driven brightness changes |
| Dynamic Contrast, Dynamic Colour | off | |
| Super Resolution, Noise Reduction, MPEG NR, Smooth Gradation | off | no processing |
| TruMotion | off | |
| Peak Brightness | high | |
| Energy Saving, Motion Eye Care | off | no automatic dimming |
| AI Brightness | off (set by hand in the menu; can't be read over the network) | |

The energy and dynamic settings were set again and read back over the network on
2026-11-05.

This is a neutral starting point, **not a calibration**: nothing was measured with a
colorimeter. To recover after a factory reset, re-apply the table above and check it with
`get_picture_settings`.

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
