"""Static scan of proof files for things that make a green build untrustworthy.

Lean: `sorry`, `axiom` declarations. Comments and string literals are ignored."""
import glob
import os
import re


def blank(text, line_comment, nested_open="/-", nested_close="-/"):
    """Return `text` with comments and string literals replaced by spaces (newlines kept, so
    line numbers stay valid)."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith(nested_open, i):
            depth, j = 1, i + len(nested_open)
            while j < n and depth:
                if text.startswith(nested_open, j):
                    depth += 1
                    j += len(nested_open)
                elif text.startswith(nested_close, j):
                    depth -= 1
                    j += len(nested_close)
                else:
                    j += 1
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
        elif text.startswith(line_comment, i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif c == '"' and not (i > 0 and text[i - 1] == "'" and text[i + 1:i + 2] == "'"):
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


LEAN_BAD = [(re.compile(r"\bsorry\b"), "sorry"), (re.compile(r"\baxiom\b"), "axiom")]


def _scan(root, folder, ext, skip, bad, **kw):
    found = []
    for p in sorted(glob.glob(os.path.join(root, folder, "**", "*" + ext), recursive=True)):
        if set(skip) & set(p.split(os.sep)):
            continue
        with open(p, encoding="utf-8") as f:
            clean = blank(f.read(), **kw)
        for no, line in enumerate(clean.splitlines(), 1):
            for rx, what in bad:
                if rx.search(line):
                    found.append("%s:%d: %s" % (os.path.relpath(p, root), no, what))
    return found


def scan_lean(root):
    """-> ["lean/File.lean:12: sorry", ...]"""
    return _scan(root, "lean", ".lean", (".lake",), LEAN_BAD, line_comment="--")
