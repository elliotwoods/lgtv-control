# lgtv-control

Notes and scripts for the LG OLED55B4 used as the Mac Studio's monitor. Read `README.md` first:
it records the TV's identity, how the av-frameworks daemon controls it, what has been
changed on the TV, and troubleshooting.

## Rules for agents

- Never commit the pairing profile (`brightness.json`, `pairing.sqlite`) or its contents
  (client key, TV certificate, serial). Scripts read it from
  `~/Library/Application Support/AuroraVision/av-frameworks/daemon/lg-tv/` at run time.
- Use `bscpylgtv==0.5.5` in a venv at `.venv/` (gitignored), run with `python -I`, and pass
  `timeout_connect=15` (the 2 s default times out on this TV).
- Check the TV model before sending settings, as `disable_panel_protection.py` does.
- The production brightness/volume path lives in `~/dev/av-frameworks/control-surface-router`
  (`src/system/webos.rs`); its docs are in `docs/extended/platform-support.md`. Change daemon
  behaviour there, not here.
- Whenever you change a TV setting, add a dated entry to `README.md`: what changed, how, and
  whether it was read back.
- The user has accepted the burn-in risk from turning panel protection off (2026-11-18).
  Don't turn it back on unless asked.
