# 🤖 [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) Codex Plugin

Give your [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) a tiny desk-job personality while Codex works. 🤓✨

Inspired by and grateful to [TwinPeaksTownie/reachy-mini-plugin](https://github.com/TwinPeaksTownie/reachy-mini-plugin)
for the original Reachy Mini + coding-assistant integration ideas. 💛

> **Safety:** Keep the robot’s movement area clear before enabling hooks. Keep hands, cables,
> pets, and fragile objects away from Reachy Mini, supervise motion, and disable the plugin if
> anything behaves unexpectedly.

## What it does 🎭

Reachy Mini joins the conversation: the plugin asks it to wake on a new/resumed Codex session,
starts a gentle sinusoidal head target when a prompt is submitted, and stops that loop when Codex
fires its `Stop` hook. A normal completed response gets a small success movement. 🫡

You can also request one of the plugin’s supported marker-based moves or moods. These are simple
HTTP requests to the Reachy daemon—not speech, facial-expression inference, or a guarantee that
the robot will move if the daemon or hardware is unavailable. Reachy is emotionally available in
spirit. 🥹

## Requirements 🧰

- Codex with plugin support.
- A [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) with its daemon available.

### USB Reachy Mini 🔌

1. Connect the robot over USB and open Reachy Mini Control.
2. Let the desktop app manage the connection and daemon.
3. Verify `http://localhost:8000/docs` opens on the computer running Codex.

No separate SDK install is needed for this path. Point the plugin at the daemon, not at a serial
port; do not configure `COM3`.

### Wireless Reachy Mini 📡

1. Start the Reachy daemon on the wireless robot or on the computer that can control it.
2. From the computer running Codex, verify `http://<robot-or-daemon-host>:8000/docs` opens.
3. Set `REACHY_MINI_DAEMON_URL` to that reachable HTTP address before starting Codex.

The plugin does not discover robots or configure Wi-Fi. If the daemon is not reachable from the
Codex computer, the hooks can still run but movement requests will fail harmlessly and be logged.

## Install 🚀

```text
codex plugin marketplace add .
codex plugin add reachy-mini@reachy-mini
```

Start a new Codex task, run `/hooks`, and trust the plugin’s `SessionStart`, `UserPromptSubmit`,
and `Stop` hooks. Reinstall after updating the plugin so Codex refreshes its cached copy.

The hook choreography is:

`SessionStart` → wake request 🌞  ·  `UserPromptSubmit` → breathing loop request 🌬️  ·  `Stop`
→ stop loop + success request 🎉

## Configuration ⚙️

```text
REACHY_MINI_DAEMON_URL=http://robot-host:8000
```

Default: `http://localhost:8000` (the USB/desktop-app path).

Head motion uses `/api/move/set_target` with a gentle 0.02-radian yaw amplitude. The worker starts
on `UserPromptSubmit` and stops on `Stop`; the hook does not promise continuous motion when Codex
or the daemon is unavailable.

## License

MIT. See [LICENSE](LICENSE).
