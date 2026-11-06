"""`linglab init`: create a project in the current folder from the toolkit template."""
import os
import shutil
import subprocess

from .common import TOOLKIT, read_json, write_json
from .version import toolkit_info

POINTER = ("This is a linglab project. Read utils/BOOTSTRAP.md, then utils/METHOD.md, "
           "and follow them.\n")
GITIGNORE = ".DS_Store\n__pycache__/\n*.pyc\n.lake/\n**/build/\n*.olean\n*.ilean\n*.trace\n*.hash\n_build/\n*.agdai\n"


def init_project(name, root=".", git=False, out=print):
    if os.path.exists(os.path.join(root, "brief.md")):
        out("error: brief.md already exists here; refusing to overwrite a project")
        return 1
    tpl = os.path.join(TOOLKIT, "template")
    shutil.copy(os.path.join(tpl, "brief.md"), os.path.join(root, "brief.md"))
    for sub in ("data", "custom", "literature"):
        shutil.copytree(os.path.join(tpl, sub), os.path.join(root, sub), dirs_exist_ok=True)
    os.makedirs(os.path.join(root, "report"), exist_ok=True)
    meta_path = os.path.join(root, "data", "meta.json")
    meta = read_json(meta_path, {})
    meta["title"] = name
    meta["toolkit"] = {k: v for k, v in toolkit_info().items() if k in ("version", "built", "commit")}
    write_json(meta_path, meta)
    for fn in ("AGENTS.md", "CLAUDE.md"):
        with open(os.path.join(root, fn), "w", encoding="utf-8") as f:
            f.write(POINTER)
    gi = os.path.join(root, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w") as f:
            f.write(GITIGNORE)
    if git:
        subprocess.run(["git", "init"], cwd=root, check=False)
    out("created project %r in %s" % (name, os.path.abspath(root)))
    return 0
