"""`linglab init`: create a project in the current folder from the toolkit template."""
import os
import re
import shutil
import subprocess

from .common import TOOLKIT, read_json, write_json
from .version import toolkit_info

POINTER = ("This is a linglab project. Read utils/BOOTSTRAP.md, then utils/METHOD.md, "
           "and follow them.\n")
GITIGNORE = ".DS_Store\n__pycache__/\n*.pyc\n.lake/\n**/build/\n*.olean\n*.ilean\n*.trace\n*.hash\n_build/\n"
MANAGED_SKILLS = ".linglab-managed.json"
VALID_SKILL_NAME = re.compile(r"linglab-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SKILL_NAME = re.compile(r"\A---\n(?:.*\n)*?name: *(\S+) *\n(?:.*\n)*?---\n")


def skill_name(text):
    """The `name` in a playbook's skill frontmatter, or None if it has none."""
    m = SKILL_NAME.match(text)
    return m.group(1) if m else None


def playbook_skills():
    """{name: text} for each playbook in moves/ that has skill frontmatter."""
    moves = os.path.join(TOOLKIT, "moves")
    out = {}
    for fn in sorted(os.listdir(moves)):
        with open(os.path.join(moves, fn), encoding="utf-8") as f:
            text = f.read()
        name = skill_name(text)
        if name:
            if not VALID_SKILL_NAME.fullmatch(name):
                raise ValueError("invalid playbook skill name: %r" % name)
            if name in out:
                raise ValueError("duplicate playbook skill name: %s" % name)
            out[name] = text
    return out


def managed_skills(root="."):
    """Names previously installed by this toolkit; unrelated or manually added skills are untouched."""
    path = os.path.join(root, ".claude", "skills", MANAGED_SKILLS)
    data = read_json(path, [])
    return sorted(n for n in data if isinstance(n, str) and VALID_SKILL_NAME.fullmatch(n)) if isinstance(data, list) else []


def skills_status(root="."):
    """Return outdated, missing, and retired toolkit-managed skill names."""
    want = playbook_skills()
    sk = os.path.join(root, ".claude", "skills")
    managed = managed_skills(root)
    have = {n for n in set(want) | set(managed) if os.path.isfile(os.path.join(sk, n, "SKILL.md"))}
    stale = []
    for name in sorted(have & set(want)):
        with open(os.path.join(sk, name, "SKILL.md"), encoding="utf-8") as f:
            if f.read() != want[name]:
                stale.append(name)
    return stale, sorted(set(want) - have), sorted(set(managed) - set(want))


def install_skills(root="."):
    """Install optional Claude Code copies; retire only copies recorded in the toolkit manifest."""
    want = playbook_skills()
    sk = os.path.join(root, ".claude", "skills")
    retired = set(managed_skills(root)) - set(want)
    for name, text in want.items():
        os.makedirs(os.path.join(sk, name), exist_ok=True)
        with open(os.path.join(sk, name, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(text)
    for name in retired:
        path = os.path.join(sk, name, "SKILL.md")
        if os.path.isfile(path):
            os.remove(path)
        folder = os.path.join(sk, name)
        if os.path.isdir(folder) and not os.listdir(folder):
            os.rmdir(folder)
    os.makedirs(sk, exist_ok=True)
    write_json(os.path.join(sk, MANAGED_SKILLS), sorted(want))
    return sorted(want)


def update_skills(root=".", out=print):
    """`linglab skills`: install or refresh the playbooks as Claude Code skills, saying what changed."""
    stale, missing, removed = skills_status(root)
    install_skills(root)
    for label, names in (("updated", stale), ("added", missing), ("removed", removed)):
        if names:
            out("%s: %s" % (label, ", ".join(names)))
    if not (stale or missing or removed):
        out("skills already match utils/moves/")
    return 0


def init_project(name, root=".", git=False, out=print, claude_skills=False):
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
    if claude_skills:
        install_skills(root)
    gi = os.path.join(root, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w") as f:
            f.write(GITIGNORE)
    if git:
        subprocess.run(["git", "init"], cwd=root, check=False)
    out("created project %r in %s" % (name, os.path.abspath(root)))
    return 0
