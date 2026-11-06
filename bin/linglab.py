#!/usr/bin/env python3
"""linglab: the one command-line tool of the linglab toolkit (Python 3, standard library only).

Run from a project's root: `python3 utils/bin/linglab.py <command>`. The toolkit root is found
from this file's own path; the project is the current directory."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python"))

from linglab import agdacmd, check, init, leancmd, listing, metrics, report, runcmd, zipper  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(prog="linglab", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init", help="create a project in the current folder")
    p.add_argument("name")
    p.add_argument("--git", action="store_true")
    sub.add_parser("check", help="validate data files")
    p = sub.add_parser("run", help="run the Python checker")
    p.add_argument("--theory")
    p.add_argument("--fact")
    p.add_argument("--bound", type=int, help="maximum number of models per theory")
    p.add_argument("--force", action="store_true", help="recompute cells that already have an entry")
    p = sub.add_parser("lean", help="build lean/ and record theorems as entries")
    p.add_argument("--build-only", action="store_true")
    p.add_argument("--init", action="store_true", help="copy the toolkit's Lean workspace into lean/ of the project (first use)")
    p.add_argument("--linglib", action="store_true", help="with --init: linglib mode (depend on linglib; asks nothing, downloads nothing)")
    p = sub.add_parser("agda", help="(optional) typecheck agda/ and record theorems as entries")
    p.add_argument("--build-only", action="store_true")
    p.add_argument("--init", action="store_true", help="copy the toolkit's Agda workspace into agda/ of the project (first use)")
    sub.add_parser("metrics", help="measure tagged principle chunks")
    sub.add_parser("listing", help="build Raw Facts")
    p = sub.add_parser("report", help="build report/index.html")
    p.add_argument("-o", "--output")
    sub.add_parser("version", help="print the toolkit version and build")
    sub.add_parser("zip", help="(toolkit) write dist/linglab-beta.zip")
    sub.add_parser("site", help="(toolkit) write dist/site/: the slides with the zip next to them, ready to host")
    a = ap.parse_args(argv)
    root = "."
    if a.cmd == "init":
        return init.init_project(a.name, root, a.git)
    if a.cmd == "check":
        return check.run_check(root)
    if a.cmd == "run":
        return runcmd.run_project(root, a.theory, a.fact, a.bound, a.force)
    if a.cmd == "lean":
        if a.init:
            return leancmd.init_lean(root, linglib=a.linglib)
        return leancmd.run_lean(root, a.build_only)
    if a.cmd == "agda":
        if a.init:
            return agdacmd.init_agda(root)
        return agdacmd.run_agda(root, a.build_only)
    if a.cmd == "metrics":
        metrics.write_metrics(root)
        print("wrote data/metrics.json")
        return 0
    if a.cmd == "listing":
        return listing.build_listing(root)
    if a.cmd == "report":
        return report.build_report(root, a.output)
    if a.cmd == "version":
        from linglab.version import toolkit_info, label
        i = toolkit_info(); print("linglab", label(i) + ((" (" + i["commit"] + ")") if i.get("commit") else ""))
        return 0
    if a.cmd == "zip":
        return zipper.make_zip()
    if a.cmd == "site":
        return zipper.make_site()


if __name__ == "__main__":
    sys.exit(main())
