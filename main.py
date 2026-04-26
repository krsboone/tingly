import logging
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

app = Flask(__name__)

TINGLY_TOKEN = os.environ["TINGLY_TOKEN"]
NTFY_URL = os.environ.get("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC_PREFIX = os.environ.get("NTFY_TOPIC_PREFIX", "")
PORT = int(os.environ.get("PORT", 7654))

VALID_TOPICS = {"threshold", "trading", "system"}
PRIORITY_MAP = {"urgent": "5", "high": "4", "default": "3", "low": "2"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.route("/notify", methods=["POST"])
def notify():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {TINGLY_TOKEN}":
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid JSON"}), 400

    for field in ("title", "body", "topic"):
        if not data.get(field):
            return jsonify({"error": f"missing required field: {field}"}), 400

    topic = data["topic"]
    if topic not in VALID_TOPICS:
        return jsonify({"error": f"unknown topic '{topic}', valid: {sorted(VALID_TOPICS)}"}), 400

    priority = data.get("priority", "default")
    if priority not in PRIORITY_MAP:
        return jsonify({"error": f"unknown priority '{priority}', valid: {list(PRIORITY_MAP)}"}), 400

    tags = data.get("tags", [])
    source = data.get("source", "unknown")

    log.info("notify source=%s topic=%s priority=%s title=%r", source, topic, priority, data["title"])

    headers = {
        "Title": data["title"],
        "Priority": PRIORITY_MAP[priority],
    }
    if tags:
        headers["Tags"] = ",".join(tags)

    ntfy_topic = f"{NTFY_TOPIC_PREFIX}-{topic}" if NTFY_TOPIC_PREFIX else topic

    try:
        resp = requests.post(
            f"{NTFY_URL}/{ntfy_topic}",
            data=data["body"].encode("utf-8"),
            headers=headers,
            timeout=5,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error("ntfy error: %s", e)
        return jsonify({"error": "ntfy unreachable"}), 502

    return jsonify({"ok": True, "ntfy_id": resp.json().get("id")}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
