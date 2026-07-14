import os
import signal
import sys
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "plugins" / "reachy-mini"))

from hooks import stop  # noqa: E402


class StopHookTests(unittest.TestCase):
    def test_default_endpoint_and_marker_allow_list(self):
        self.assertEqual(stop.DAEMON_URL, "http://localhost:8000")
        self.assertEqual(
            stop.extract_move_markers("<!-- MOVE: cheerful1 --><!-- MOVE: not_real -->"),
            ["cheerful1"],
        )

    def test_mood_maps_to_allow_listed_move(self):
        self.assertEqual(stop.extract_mood_marker("<!-- MOOD: thoughtful -->"), "thoughtful")
        self.assertEqual(stop.MOOD_TO_EMOTION["thoughtful"], "thoughtful1")
        self.assertEqual(stop.MOOD_TO_EMOTION["understanding"], "understanding1")
        self.assertEqual(stop.MOOD_TO_EMOTION["proud"], "proud1")
        self.assertEqual(stop.MOOD_TO_EMOTION["attentive"], "attentive1")

    def test_endpoint_override_is_plugin_specific(self):
        with patch.dict(os.environ, {stop.DAEMON_ENV: "http://robot-host:8000"}), patch(
            "hooks.stop.post_json", return_value=True
        ) as post_json:
            stop.trigger_move("thoughtful1")

        self.assertTrue(post_json.call_args.args[0].startswith("http://robot-host:8000/"))

    def test_ordinary_response_gets_celebration(self):
        with TemporaryDirectory() as data_root, TemporaryDirectory() as files_root:
            transcript = Path(files_root) / "transcript.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "phase": "final_answer",
                            "content": [{"type": "output_text", "text": "The fix is done."}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"PLUGIN_DATA": data_root}), patch(
                "hooks.stop.post_json", return_value=True
            ) as post_json:
                stop.handle_event({"turn_id": "automatic-move", "transcript_path": str(transcript)})

        self.assertTrue(post_json.call_args.args[0].endswith("/success1"))

    def test_session_and_prompt_lifecycle_moves(self):
        with patch("hooks.stop.post_json", return_value=True) as post_json, patch(
            "hooks.stop.subprocess.Popen"
        ) as popen:
            popen.return_value.pid = 123
            stop.handle_lifecycle("session-start")
            stop.handle_lifecycle("prompt-submit")

        urls = [call.args[0] for call in post_json.call_args_list]
        self.assertTrue(urls[0].endswith("/api/move/play/wake_up"))
        self.assertTrue(urls[1].endswith("/yes1"))
        self.assertTrue(urls[2].endswith("/thoughtful1"))
        popen.assert_called_once()

    def test_head_target_is_small_sinusoidal_yaw(self):
        with patch("hooks.stop.post_json", return_value=True) as post_json:
            stop.trigger_head_target(stop.HEAD_MOTION_AMPLITUDE)

        payload = post_json.call_args.args[1]
        self.assertEqual(payload["target_head_pose"]["yaw"], stop.HEAD_MOTION_AMPLITUDE)


if __name__ == "__main__":
    unittest.main()
