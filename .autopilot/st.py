"""Tiny state.js editor for the orchestrator.

python .autopilot/st.py ticket 05 status=in-progress startedAt=now
python .autopilot/st.py stage review status=active startedAt=now note="проверяется 01"
python .autopilot/st.py set requirements.done=12 tests.passed=40
Values: `now` -> current ISO time; ints parsed; `json:<...>` parsed as JSON.
"""
import json
import os
import subprocess
import sys
from datetime import datetime

A = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(A, "state.js")


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def val(v):
    if v == "now":
        return now()
    if v.startswith("json:"):
        return json.loads(v[5:])
    if v.lstrip("-").isdigit():
        return int(v)
    return v


def main():
    head, body = open(P, encoding="utf-8").read().split("\n", 1)
    st = json.loads(body)
    kind, rest = sys.argv[1], sys.argv[2:]
    if kind in ("ticket", "stage"):
        key, rest = rest[0], rest[1:]
        rows = st["tickets"] if kind == "ticket" else st["stages"]
        target = next(r for r in rows if r["id"] == key)
    else:
        target = st
    for kv in rest:
        k, v = kv.split("=", 1)
        obj = target
        parts = k.split(".")
        for p in parts[:-1]:
            if obj.get(p) is None:
                obj[p] = {}
            obj = obj[p]
        obj[parts[-1]] = val(v)
    st["updatedAt"] = now()
    open(P, "w", encoding="utf-8").write(head + "\n" + json.dumps(st, ensure_ascii=False, indent=2) + "\n")
    env = dict(os.environ, CI="1", PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, os.path.join(A, "sync.py")], env=env)


if __name__ == "__main__":
    main()
