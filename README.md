# Reachy Mini Codex Plugin

Reachy Mini movements for Codex conversations.

## Features

- Wake on session start.
- Nod and think on each prompt.
- Gentle sinusoidal head motion while Codex thinks and responds.
- Small success movement when the response ends.
- Explicit `$reachy-mini:reachy-mini-move` and `$reachy-mini:reachy-mini-mood` overrides.

## Requirements

- Codex with plugin support.
- Reachy Mini Control open with its daemon available at `http://localhost:8000`.

The desktop app manages the USB connection. No separate SDK install is needed. Check
`http://localhost:8000/docs` if movement is not working; do not configure `COM3`.

## Install

```text
codex plugin marketplace add .
codex plugin add reachy-mini@reachy-mini
```

Start a new Codex task, run `/hooks`, and trust the plugin’s `SessionStart`, `UserPromptSubmit`,
and `Stop` hooks. Reinstall after updating the plugin so Codex refreshes its cached copy.

## Configuration

```text
REACHY_MINI_DAEMON_URL=http://robot-host:8000
```

Default: `http://localhost:8000`.

## Development

```text
python -m unittest discover -s tests -v
python -m compileall plugins/reachy-mini/hooks tests
```

Head motion uses `/api/move/set_target` with a gentle 0.02-radian yaw amplitude. The worker starts
on `UserPromptSubmit` and stops on `Stop`.

## License

MIT. See [LICENSE](LICENSE).
