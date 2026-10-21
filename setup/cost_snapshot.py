"""Runs each query in cost_snapshot.sql with the Snowflake CLI (connection "wbr") and prints the results.
A query that fails (missing view, no ACCOUNT_USAGE access) is reported and the rest still run."""
import os, re, shutil, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
sql = open(os.path.join(here, "cost_snapshot.sql"), encoding="utf-8").read()
blocks = [b.strip() for b in re.split(r";\s*\n", sql) if b.strip() and re.search(r"\bSELECT\b|\bWITH\b", b)]
snow = shutil.which("snow") or "snow"
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
# Optional: a role that can read SNOWFLAKE.ACCOUNT_USAGE, e.g. run_cost_snapshot.cmd ACCOUNTADMIN
role = sys.argv[1] if len(sys.argv) > 1 else ""
for b in blocks:
    title = next((l[3:].strip() for l in b.splitlines() if re.match(r"--\s*\d\)", l)), "query")
    # one line, no comments: multi-line arguments get cut at the first line break on Windows
    stmt = " ".join(l.strip() for l in b.splitlines() if l.strip() and not l.strip().startswith("--"))
    print("=" * 100 + "\n" + title + "\n" + "=" * 100, flush=True)
    cmd = [snow, "sql", "-c", "wbr"] + (["--role", role] if role else []) + ["-q", stmt]
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8",
                       errors="replace", env=env)
    out = (r.stdout or "").strip()
    err = "\n".join(l for l in (r.stderr or "").splitlines()
                    if "Encoding mismatch" not in l and "warnings.warn" not in l).strip()
    if r.returncode == 0:
        print(out[-20000:], flush=True)
    else:
        print("FAILED (exit %s)\n%s\n%s" % (r.returncode, out[-3000:], err[-3000:]), flush=True)
