"""`linglab zip`: package the toolkit as dist/linglab-beta.zip (top folder linglab/)."""
import datetime
import json
import os
import zipfile

from .common import TOOLKIT
from .version import build_info, label

SKIP_DIRS = {".git", "dist", "__pycache__", ".lake", "build", "_build", ".claude", "out"}
SKIP_FILES = {".DS_Store", ".git"}   # ".git" can be a file (worktree pointer): never ship it
# Tests and contributor instructions are not needed in the downloadable kit.
SKIP_PATHS = ("python/tests", "CONTRIBUTING.md")
SKIP_EXT = (".pyc", ".olean", ".ilean", ".trace", ".hash", ".agdai")


def make_zip(out=print):
    dest = os.path.join(TOOLKIT, "dist", "linglab-beta.zip")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    n = 0
    info = build_info(datetime.date.today().isoformat())
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("linglab/BUILD.json", json.dumps(info, indent=2) + "\n")
        for base, dirs, files in os.walk(TOOLKIT):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
                             and os.path.relpath(os.path.join(base, d), TOOLKIT).replace(os.sep, "/") not in SKIP_PATHS)
            for fn in sorted(files):
                if fn in SKIP_FILES or fn.endswith(SKIP_EXT):
                    continue
                p = os.path.join(base, fn)
                rel = os.path.relpath(p, TOOLKIT).replace(os.sep, "/")
                if any(rel == x or rel.startswith(x + "/") for x in SKIP_PATHS):
                    continue
                z.write(p, os.path.join("linglab", os.path.relpath(p, TOOLKIT)))
                n += 1
    out("wrote %s (%d files, %s)" % (dest, n, label(info)))
    return 0


def make_site(out=print):
    """`linglab site`: dist/site/ = the slides (index.html, examples.html) with the zip next to them, ready to host."""
    import shutil
    zipf = os.path.join(TOOLKIT, "dist", "linglab-beta.zip")
    if not os.path.exists(zipf):
        make_zip(out)
    import zipfile as _zf
    zinfo = json.loads(_zf.ZipFile(zipf).read("linglab/BUILD.json").decode("utf-8"))
    site = os.path.join(TOOLKIT, "dist", "site")
    shutil.rmtree(site, ignore_errors=True)
    os.makedirs(site)
    for name in ("index.html", "examples.html"):
        src = os.path.join(TOOLKIT, "slides", name)
        if os.path.exists(src):
            text = open(src, encoding="utf-8").read().replace("../dist/linglab-beta.zip", "linglab-beta.zip")
            text = text.replace("{{VERSION}}", label(zinfo))
            open(os.path.join(site, name), "w", encoding="utf-8").write(text)
    shutil.copy(zipf, os.path.join(site, "linglab-beta.zip"))
    open(os.path.join(site, ".nojekyll"), "w").close()
    out("wrote %s (slides + zip %s)" % (site, label(zinfo)))
    return 0
