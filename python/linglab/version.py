"""Toolkit version: VERSION (always shipped) and BUILD.json (written into the zip by `linglab zip`)."""
import json
import os
import subprocess

from .common import TOOLKIT


def _git(*args):
    try:
        r = subprocess.run(["git"] + list(args), cwd=TOOLKIT, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def toolkit_info():
    """{'version', 'built', 'commit'}: from BUILD.json if present (an unzipped package), else from VERSION and git (a checkout)."""
    b = os.path.join(TOOLKIT, "BUILD.json")
    if os.path.exists(b):
        try:
            return json.load(open(b, encoding="utf-8"))
        except Exception:
            pass
    v = "unknown"
    try:
        v = open(os.path.join(TOOLKIT, "VERSION"), encoding="utf-8").read().strip() or v
    except OSError:
        pass
    return {"version": v, "built": "", "commit": _git("rev-parse", "--short", "HEAD"), "dev": True}


def build_info(today):
    """For `linglab zip`: version, build date and commit (with a dirty flag)."""
    info = toolkit_info()
    commit = _git("rev-parse", "--short", "HEAD")
    if commit and _git("status", "--porcelain"):
        commit += "+dirty"
    return {"version": info["version"], "built": today, "commit": commit}


def label(info):
    s = "v" + info.get("version", "?")
    if info.get("built"):
        s += ", built " + info["built"]
    return s
