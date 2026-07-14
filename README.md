# Reachy Mini Codex Plugin

Automatic Reachy Mini lifecycle movements for natural Codex conversations, with explicit overrides.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Reachy Mini](https://img.shields.io/badge/Reachy-Mini-orange.svg)](https://www.pollen-robotics.com/reachy-mini/)

## What it does

- `SessionStart` plays `wake_up`.
- `UserPromptSubmit` plays a nod (`yes1`) followed by the thinking gesture (`thoughtful1`).
- `Stop` plays a small celebration (`success1`) when the response finishes.
- During thinking and response generation, the head makes a subtle sinusoidal yaw movement.
- `$reachy-mini:reachy-mini-move` and `$reachy-mini:reachy-mini-mood` remain explicit overrides.
- Robot daemon outages are logged and do not stop Codex.

The lifecycle hooks are automatic once trusted. Installing the plugin alone does not run movement until
the hooks are reviewed and trusted.

## Requirements

- Codex with plugin support
- Reachy Mini Control desktop app running its local daemon at `http://localhost:8000`

Override local endpoints when needed:

```text
REACHY_MINI_DAEMON_URL=http://robot-host:8000
```

Open Reachy Mini Control and leave it running. It starts the local daemon and handles the USB
connection automatically. Verify `http://localhost:8000/docs` if you want to confirm the daemon is
available; do not point the plugin at `COM3` directly.

The standalone SDK daemon is only needed for a manual, non-desktop-app setup.

## Install from this repository

From the repository root:

```text
codex plugin marketplace add .
codex plugin list
codex plugin add reachy-mini@reachy-mini
```

Start a new Codex task after installation. Open `/hooks`, review the plugin hooks, and trust them before testing movement.

Activation is a one-time safety step per installed hook:

1. Start a new Codex task after installing or reinstalling the plugin.
2. Run `/hooks`.
3. Select the `SessionStart`, `UserPromptSubmit`, and `Stop` hooks from `reachy-mini@reachy-mini`, review them, and press `t` to trust them.
4. Start another new task. Hooks that are shown as `Review 1` or `Active 0` cannot send requests.

Codex intentionally requires this review because a Stop hook can run outside the sandbox. The plugin
cannot trust itself programmatically.

## Use

The normal lifecycle is automatic. Explicitly invoke a skill only when you want to override the
movement for the current response:

```text
$reachy-mini:reachy-mini-move
```

or:

```text
$reachy-mini:reachy-mini-mood
```

`@reachy-mini:reachy-mini-move` and `@reachy-mini:reachy-mini-mood` are also accepted by Codex. The
skill only adds an invisible marker; the trusted Stop hook performs the network request after the
response finishes.

The skills add invisible markers; the trusted Stop hook performs the override request after the
response finishes. The raw markers are HTML comments, so they remain invisible in rendered Markdown. `MOOD` markers
are translated to one recorded move by the Stop hook; the separate Reachy conversation app is
optional:

```html
<!-- MOVE: thoughtful1 -->
<!-- MOOD: celebratory -->
```

## Hook behavior

The lifecycle hooks map directly to the conversation: wake on session start, nod and think on a new
user prompt, then celebrate on the final answer. The Stop hook parses Codex JSONL transcripts for the
latest assistant `final_answer`, ignores malformed records and invalid markers, allows up to two
explicit moves, maps an explicit mood to one recorded move, and deduplicates repeated Stop events
by `turn_id`. The turn is claimed before network dispatch so replayed events cannot duplicate robot
motion; an unavailable endpoint is not retried automatically.

The transcript format is a Codex implementation detail. The parser is isolated in
`plugins/reachy-mini/hooks/stop.py` and intentionally fails closed when expected fields are absent.

## Development checks

```text
python -m unittest discover -s tests -v
python -m compileall plugins/reachy-mini/hooks tests
```

The manifest's `hooks` field registers plugin lifecycle hooks. Use the tests and JSON parsing above
to validate changes.

Hardware acceptance requires a running daemon and one smoke test for session start, prompt submit,
completion, and explicit marker overrides.

Head motion uses the daemon’s `/api/move/set_target` endpoint with a gentle 0.02-radian yaw amplitude.

## Troubleshooting

- **Reachy does not move automatically:** run `/hooks` and check that all three plugin hooks are
  `Active`, not `Review` or `Active 0`; then retry in a new task.
- **The log shows `127.0.0.1:9`:** reinstall this plugin, then fully restart Codex. The plugin uses
  `REACHY_MINI_DAEMON_URL` and otherwise defaults to `http://localhost:8000`; it ignores the old
  generic `REACHY_DAEMON_URL` override from the Claude setup.
- **The hook runs but no robot is connected:** check the daemon URL and inspect the plugin log under
  `%USERPROFILE%\\.codex\\plugins\\data\\reachy-mini-reachy-mini\\reachy-mini.log`.
- **A newly installed version is not picked up:** reinstall the plugin and start a new Codex task.

## Attribution

This is a Codex adaptation of the original Reachy Mini Claude Code plugin by
[LAURA-agent](https://github.com/LAURA-agent). The MIT license and original copyright notice are
retained. Claude and Codex are tools used to develop the project, not the copyright holders.

## License

MIT. See [LICENSE](LICENSE).
