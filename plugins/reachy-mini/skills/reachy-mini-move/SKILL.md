---
name: reachy-mini-move
description: Add one or two explicit Reachy Mini emotion markers to the current Codex response when the user asks for a robot gesture or reaction.
---

# Reachy Mini movement

The Stop hook already chooses a gesture automatically. Use this skill only when the user explicitly
invokes `$reachy-mini:reachy-mini-move` and wants to override that choice.

Add zero, one, or two invisible HTML comments to the response:

```html
<!-- MOVE: emotion_name -->
```

Choose only an emotion from the supported Reachy Mini library. Verified defaults include `thoughtful1`, `curious1`, `attentive1`, `cheerful1`, `success1`, `surprised1`, `confused1`, `calming1`, and `yes1`; use `thoughtful1` if unsure. Match the gesture to the response, keep it subtle, and never add more than two markers. Do not invent a new emotion name. The marker is intentionally invisible in rendered Markdown.
