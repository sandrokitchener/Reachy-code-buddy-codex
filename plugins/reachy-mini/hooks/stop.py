#!/usr/bin/env python3
"""Trigger Reachy Mini movement markers emitted by a Codex response."""

from __future__ import annotations

import json
import hashlib
import logging
import math
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DAEMON_URL = "http://localhost:8000"
DAEMON_ENV = "REACHY_MINI_DAEMON_URL"
DATASET = "pollen-robotics/reachy-mini-emotions-library"
REQUEST_TIMEOUT = 1.0
MAX_SEEN_TURNS = 256
HEAD_MOTION_MODE_ENV = "REACHY_MINI_HEAD_MOTION"
HEAD_MOTION_PID = "head-motion.pid"
HEAD_MOTION_AMPLITUDE = 0.02
HEAD_MOTION_FREQUENCY = 0.08
HEAD_MOTION_INTERVAL = 0.05

EMOTIONS = {
    "amazed1", "anxiety1", "attentive1", "attentive2", "boredom1", "boredom2",
    "calming1", "cheerful1", "come1", "confused1", "contempt1", "curious1",
    "dance1", "dance2", "dance3", "disgusted1", "displeased1", "displeased2",
    "downcast1", "dying1", "electric1", "enthusiastic1", "enthusiastic2",
    "exhausted1", "fear1", "frustrated1", "furious1", "go_away1", "grateful1",
    "helpful1", "helpful2", "impatient1", "impatient2", "incomprehensible2",
    "indifferent1", "inquiring1", "inquiring2", "inquiring3", "irritated1",
    "irritated2", "laughing1", "laughing2", "lonely1", "lost1", "loving1",
    "no1", "no_excited1", "no_sad1", "oops1", "oops2", "proud1", "proud2",
    "proud3", "rage1", "relief1", "relief2", "reprimand1", "reprimand2",
    "reprimand3", "resigned1", "sad1", "sad2", "scared1", "serenity1", "shy1",
    "sleep1", "success1", "success2", "surprised1", "surprised2", "thoughtful1",
    "thoughtful2", "tired1", "uncertain1", "uncomfortable1", "understanding1",
    "understanding2", "welcoming1", "welcoming2", "yes1", "yes_sad1",
}
MOOD_TO_EMOTION = {
    "celebratory": "success1",
    "thoughtful": "thoughtful1",
    "welcoming": "welcoming1",
    "confused": "confused1",
    "frustrated": "frustrated1",
    "surprised": "surprised1",
    "calm": "calming1",
    "energetic": "enthusiastic1",
    "playful": "cheerful1",
    "understanding": "understanding1",
    "proud": "proud1",
    "attentive": "attentive1",
}
MOODS = set(MOOD_TO_EMOTION)

MOVE_PATTERN = re.compile(r"<!--\s*MOVE:\s*([a-zA-Z0-9_]+)\s*-->")
MOOD_PATTERN = re.compile(r"<!--\s*MOOD:\s*([a-zA-Z0-9_]+)\s*-->")
LOGGER = logging.getLogger("reachy-mini")


def configure_logging() -> None:
    data_root = os.environ.get("PLUGIN_DATA")
    log_path = (
        Path(data_root) / "reachy-mini.log"
        if data_root
        else Path(os.getenv("TEMP", "/tmp")) / "reachy-mini.log"
    )
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s %(message)s")
    except OSError:
        logging.basicConfig(level=logging.ERROR)


def extract_final_response(transcript_path: Path) -> str:
    """Return the latest Codex assistant final answer from a JSONL transcript."""
    response = ""
    try:
        with transcript_path.open(encoding="utf-8", errors="replace") as transcript:
            for line in transcript:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                payload = record.get("payload")
                if not isinstance(payload, dict):
                    continue
                if (
                    record.get("type") == "response_item"
                    and payload.get("type") == "message"
                    and payload.get("role") == "assistant"
                    and payload.get("phase") == "final_answer"
                ):
                    content = payload.get("content")
                    if not isinstance(content, list):
                        response = ""
                        continue
                    response = "".join(
                        block.get("text", "")
                        for block in content
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "output_text"
                            and isinstance(block.get("text", ""), str)
                        )
                    )
    except OSError:
        return ""
    return response


def extract_move_markers(text: str) -> list[str]:
    return [emotion for emotion in MOVE_PATTERN.findall(text) if emotion in EMOTIONS][:2]


def extract_mood_marker(text: str) -> str | None:
    match = MOOD_PATTERN.search(text)
    return match.group(1) if match and match.group(1) in MOODS else None


def post_json(url: str, payload: dict | None = None) -> bool:
    try:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        request = Request(url, data=data, headers=headers, method="POST")
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return 200 <= response.status < 300
    except (HTTPError, URLError, OSError, TimeoutError, TypeError, ValueError) as error:
        LOGGER.warning("request failed for %s: %s", url, error)
        return False


def trigger_move(emotion: str) -> bool:
    url = f"{os.environ.get(DAEMON_ENV, DAEMON_URL).rstrip('/')}/api/move/play/recorded-move-dataset/{DATASET}/{emotion}"
    return post_json(url)


def trigger_wake_up() -> bool:
    url = f"{os.environ.get(DAEMON_ENV, DAEMON_URL).rstrip('/')}/api/move/play/wake_up"
    return post_json(url)


def state_path() -> Path:
    return Path(os.environ.get("PLUGIN_DATA", os.getenv("TEMP", "/tmp")))


def trigger_head_target(yaw: float) -> bool:
    url = f"{os.environ.get(DAEMON_ENV, DAEMON_URL).rstrip('/')}/api/move/set_target"
    return post_json(
        url,
        {"target_head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": 0, "yaw": yaw}},
    )


def head_motion_worker() -> int:
    started = time.monotonic()
    while True:
        elapsed = time.monotonic() - started
        trigger_head_target(
            HEAD_MOTION_AMPLITUDE * math.sin(2 * math.pi * HEAD_MOTION_FREQUENCY * elapsed)
        )
        time.sleep(HEAD_MOTION_INTERVAL)


def stop_head_motion() -> None:
    pid_file = state_path() / HEAD_MOTION_PID
    try:
        pid = int(pid_file.read_text(encoding="ascii"))
        os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError):
        pass
    try:
        pid_file.unlink()
    except OSError:
        pass


def start_head_motion() -> None:
    stop_head_motion()
    if os.environ.get(HEAD_MOTION_MODE_ENV, "sinusoidal").lower() == "off":
        return
    state_path().mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "head-motion"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    (state_path() / HEAD_MOTION_PID).write_text(str(process.pid), encoding="ascii")


def mark_turn_seen(turn_id: str | None, event_name: str = "stop") -> bool:
    # Claim before network I/O: replayed Stop events must not duplicate motion.
    if not isinstance(turn_id, str) or not turn_id:
        return False
    data_root = os.environ.get("PLUGIN_DATA")
    if not data_root:
        return False
    data_dir = Path(data_root)
    seen_dir = data_dir / "seen-turns"
    key = f"{event_name}:{turn_id}"
    marker = seen_dir / f"{hashlib.sha256(key.encode('utf-8')).hexdigest()}.seen"
    try:
        seen_dir.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return True
        os.close(descriptor)
        markers = sorted(seen_dir.glob("*.seen"), key=lambda path: path.stat().st_mtime, reverse=True)
        for stale_marker in markers[MAX_SEEN_TURNS:]:
            try:
                stale_marker.unlink()
            except OSError:
                continue
    except OSError:
        return False
    return False


def handle_event(event: dict) -> int:
    if not isinstance(event, dict):
        return 0
    transcript = event.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        return 0
    response = extract_final_response(Path(transcript))
    moves = extract_move_markers(response)
    mood = extract_mood_marker(response)
    if not moves and not mood and response.strip():
        moves = [MOOD_TO_EMOTION["celebratory"]]
    if not moves and not mood:
        return 0
    if mark_turn_seen(event.get("turn_id"), "stop"):
        return 0

    for emotion in moves:
        trigger_move(emotion)
    if mood:
        trigger_move(MOOD_TO_EMOTION[mood])
    return 0


def handle_lifecycle(event_name: str) -> int:
    if event_name == "session-start":
        trigger_wake_up()
    elif event_name == "prompt-submit":
        start_head_motion()
        trigger_move("yes1")
        trigger_move("thoughtful1")
    return 0


def main() -> int:
    configure_logging()
    if len(sys.argv) > 1 and sys.argv[1] == "head-motion":
        return head_motion_worker()
    if len(sys.argv) > 1:
        if sys.argv[1] == "session-start":
            stop_head_motion()
        return handle_lifecycle(sys.argv[1])
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    stop_head_motion()
    return handle_event(event)


if __name__ == "__main__":
    raise SystemExit(main())
