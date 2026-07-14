---
name: reachy-mini-mood
description: Add one explicit Reachy Mini mood marker to the current Codex response when the user asks for sustained robot movement.
---

# Reachy Mini mood

The Stop hook already chooses a mood automatically. Use this skill only when the user explicitly
invokes `$reachy-mini:reachy-mini-mood` and wants to override that choice.

Add one invisible HTML comment to the response:

```html
<!-- MOOD: mood_name -->
```

Choose one of: `celebratory`, `thoughtful`, `welcoming`, `confused`, `frustrated`, `surprised`, `calm`, `energetic`, `playful`, `understanding`, `proud`, or `attentive`. Match the mood to the response. Do not add more than one mood marker. The Codex Stop hook maps the mood to one allow-listed recorded emotion and sends it to the Reachy daemon; it does not run a long-lived TTS loop or require the conversation app.
