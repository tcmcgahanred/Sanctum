#!/usr/bin/env python3
"""
Sanctum · tools/sensor_check.py · the sensor health check

Fetches every sensor a domain declares and reports what actually came back.

WHY THIS EXISTS
---------------
A sensor can be configured, listed, and contributing nothing, with no error
raised anywhere. The run completes. The item count is quietly lower. The sensor
list claims coverage that does not exist.

Three real examples, all live in production and none detectable at the time:

    a maritime feed   301 to a host behind bot protection returning 403
    Packet Storm      HTTP 200, serves a webpage, zero feed items
    Fortiguard        HTTP 500, serves an HTML error page

Packet Storm is the instructive one. It returns 200, so any check that trusts
the status code passes it. **Count the items. Do not infer health from a status
code.** That is the whole design principle of this tool, and the reason it
fetches rather than pings.

The reverse error is just as real: a first crude pass over the CTI sensors
flagged three healthy feeds as dead — a byte-order mark, rate-limiting caused by
the probing itself, and a suppressed status header. A checker that cries wolf
gets ignored, so this one reports what it saw and reserves DEAD for "returned
no items."

WHAT IT REPORTS PER SENSOR
    items      how many entries the feed yielded          <- the number that matters
    status     HTTP status, or "-" if the library hid it
    redirect   the final URL, when it differs from the one configured
    parse      whether the body parsed as a feed at all
    verdict    OK / EMPTY / UNPARSEABLE / ERROR

RUN IT FROM THE COLLECTOR HOST, NOT YOUR WORKSTATION. Several publishers serve
a browser normally and return 403 to a datacentre address. A sensor verified
from a laptop can be dead in production, which is exactly how the maritime feed
was admitted.

USAGE
    tools/sensor_check.py cti
    tools/sensor_check.py cti --timeout 30
    tools/sensor_check.py --pnd path/to/pnd.md
    tools/sensor_check.py cti --only-problems

EXIT CODES
    0  every sensor returned at least one item
    1  at least one sensor returned nothing, or the domain failed to load
"""

import argparse
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pnd import load_domain   # noqa: E402

try:
    import feedparser
except ImportError:  # pragma: no cover
    raise SystemExit("sensor_check needs feedparser: pip install feedparser")

OK, EMPTY, UNPARSEABLE, ERROR = "OK", "EMPTY", "UNPARSEABLE", "ERROR"


def check_one(url):
    """
    Fetch one sensor and describe what came back. Never raises — a checker that
    dies on the first bad URL cannot report on the rest.
    """
    r = {"url": url, "items": 0, "status": None, "final_url": None,
         "parsed": False, "verdict": ERROR, "note": ""}
    try:
        p = feedparser.parse(url)
    except Exception as e:
        r["note"] = f"{type(e).__name__}: {e}"
        return r

    r["items"] = len(getattr(p, "entries", []) or [])
    r["status"] = getattr(p, "status", None)
    final = getattr(p, "href", None)
    if final and final.rstrip("/") != url.rstrip("/"):
        r["final_url"] = final
    bozo = bool(getattr(p, "bozo", 0))
    r["parsed"] = not bozo

    if bozo:
        exc = getattr(p, "bozo_exception", None)
        r["note"] = f"{type(exc).__name__}: {exc}" if exc else "malformed feed"

    # Items first. A feed can be flagged malformed and still yield usable
    # entries — a stray byte-order mark does that — and throwing those away
    # would be the false alarm this tool exists to avoid.
    if r["items"] > 0:
        r["verdict"] = OK
        if bozo:
            r["note"] = f"parsed with warnings ({r['note']}) but returned items"
    elif bozo:
        r["verdict"] = UNPARSEABLE
    else:
        r["verdict"] = EMPTY
        if not r["note"]:
            r["note"] = ("well-formed feed, zero entries — genuinely quiet, "
                         "or serving something that is not this feed")
    return r


def render(domain, results, only_problems=False):
    lines = []
    bad = [r for r in results if r["verdict"] != OK]
    shown = bad if only_problems else results

    lines.append(f"\nSENSOR CHECK — {domain}: {len(results)} sensors, "
                 f"{len(results) - len(bad)} returning items, {len(bad)} not\n")

    # EVERYTHING FAILING THE SAME WAY MEANS THE PROBLEM IS HERE, NOT THERE.
    # Found while testing this tool: run from a sandbox behind an egress proxy,
    # all four sensors returned an identical 403 — including two that are
    # certainly healthy. Without this line the output reads as four dead feeds
    # and someone deletes working sensors.
    if len(results) > 2 and len(bad) == len(results):
        notes = {r["note"].split(":")[0] for r in results if r["note"]}
        if len(notes) == 1:
            lines.append("  *** EVERY SENSOR FAILED, ALL THE SAME WAY. That is almost")
            lines.append("      certainly this machine's network path, not the sensors.")
            lines.append("      Are you running from the collector host? Do not remove")
            lines.append("      anything on the strength of this run. ***\n")
    lines.append(f"  {'ITEMS':>5}  {'STATUS':>6}  {'VERDICT':<12}  URL")
    lines.append(f"  {'-'*5}  {'-'*6}  {'-'*12}  {'-'*40}")
    for r in sorted(shown, key=lambda x: (x["verdict"] == OK, -x["items"])):
        st = r["status"] if r["status"] is not None else "-"
        lines.append(f"  {r['items']:>5}  {str(st):>6}  {r['verdict']:<12}  {r['url']}")
        if r["final_url"]:
            lines.append(f"         redirected to: {r['final_url']}")
        if r["note"]:
            lines.append(f"         {r['note']}")

    if bad:
        lines.append("\nA status of 200 proves nothing — one of the sensors this tool was")
        lines.append("written for returns 200 and serves a webpage. Read the ITEMS column.")
        lines.append("Re-test before removing anything: rate-limiting caused by probing")
        lines.append("itself has produced false alarms here.")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fetch every sensor a domain declares and report what came back.")
    ap.add_argument("domain", nargs="?", help="domain name")
    ap.add_argument("--pnd", help="explicit path to a pnd.md")
    ap.add_argument("--timeout", type=int, default=20,
                    help="socket timeout in seconds (default 20)")
    ap.add_argument("--only-problems", action="store_true",
                    help="list only sensors that returned nothing")
    args = ap.parse_args(argv)

    if not (args.domain or args.pnd):
        ap.error("give a domain name or --pnd")

    # feedparser offers no timeout argument, so set it globally. Without this a
    # single stalled host can hang the whole check, which is the same defect the
    # collector has and is on the backlog there.
    socket.setdefaulttimeout(args.timeout)

    try:
        cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    except Exception as e:
        print(f"sensor_check: could not load domain — {e}", file=sys.stderr)
        return 1

    urls = cfg["sensors"]
    if not urls:
        print(f"sensor_check: [{cfg['domain']}] declares no sensors")
        return 1

    print(f"sensor_check: fetching {len(urls)} sensors for [{cfg['domain']}] "
          f"(timeout {args.timeout}s)...", file=sys.stderr)
    results = [check_one(u) for u in urls]
    print(render(cfg["domain"], results, args.only_problems))
    return 1 if any(r["verdict"] != OK for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
