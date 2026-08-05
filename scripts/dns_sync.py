"""Point auditagent.ca at GitHub Pages via the GoDaddy Domains API (v1).

Plans by default; applies only with --apply. Run from GitHub Actions, where the
token lives in Actions Secrets and never touches a laptop.

    GODADDY_PAT=... GITHUB_USER=... python scripts/dns_sync.py
    GODADDY_PAT=... GITHUB_USER=... python scripts/dns_sync.py --apply

Only three (type, name) pairs are managed: A/@, AAAA/@, CNAME/www. Everything
else in the zone — MX, TXT, anything carrying mail or domain verification — is
reported and left alone.

## API notes, verified against this account rather than assumed

- **v1, not v3.** The v3 `/v3/domains/zones/{zone}/dns-records` endpoints
  return 404 for a normal (non-reseller) account. v1 is the surface that works.
- **Bearer, not sso-key.** `Authorization: Bearer <PAT>`. The older
  `sso-key KEY:SECRET` scheme returns 401.
- **PUT replaces every record of one type+name.** `PUT /records/{type}/{name}`
  with an array body is atomic for that pair, so GoDaddy's parking records for
  A/@ disappear as a side effect of writing the real ones. No delete pass, and
  no window where the apex resolves to nothing.
"""

from __future__ import annotations

import argparse
import os
import sys

import requests

BASE = "https://api.godaddy.com/v1/domains"
DOMAIN = "auditagent.ca"

# GitHub Pages apex addresses. Re-check GitHub's "Managing a custom domain"
# doc before a first setup — these change rarely, but they do change.
PAGES_A = [
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153",
]
PAGES_AAAA = [
    "2606:50c0:8000::153",
    "2606:50c0:8001::153",
    "2606:50c0:8002::153",
    "2606:50c0:8003::153",
]

# GoDaddy rejects a TTL below 600.
TTL = 600

MANAGED = {("A", "@"), ("AAAA", "@"), ("CNAME", "www")}


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"error: {name} is not set")
    return value


def fmt(record: dict) -> str:
    return (f"    {record.get('type', '?'):<6} {record.get('name', '?'):<6} "
            f"{record.get('data', '?'):<40} ttl={record.get('ttl')}")


def list_records(session: requests.Session) -> list[dict]:
    resp = session.get(f"{BASE}/{DOMAIN}/records", timeout=30)
    if resp.status_code == 401:
        sys.exit("error: GoDaddy rejected the token (401) — expired, or wrong auth scheme.")
    if resp.status_code == 403:
        sys.exit("error: token lacks permission for this domain (403).")
    if resp.status_code == 404:
        sys.exit(
            f"error: {DOMAIN} not found in this GoDaddy account (404).\n"
            f"       The token belongs to an account that does not hold this domain."
        )
    resp.raise_for_status()
    return resp.json()


def desired() -> dict[tuple[str, str], list[dict]]:
    """Target records, grouped by the (type, name) pair each PUT replaces."""
    github_user = env("GITHUB_USER")
    return {
        ("A", "@"): [{"data": ip, "ttl": TTL} for ip in PAGES_A],
        ("AAAA", "@"): [{"data": ip, "ttl": TTL} for ip in PAGES_AAAA],
        ("CNAME", "www"): [{"data": f"{github_user}.github.io", "ttl": TTL}],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="apply the plan; without this the script only reports")
    args = parser.parse_args()

    pat = env("GODADDY_PAT")
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {pat}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })

    current = list_records(session)
    targets = desired()

    in_scope = [r for r in current if (r.get("type"), r.get("name")) in MANAGED]
    out_of_scope = [r for r in current if (r.get("type"), r.get("name")) not in MANAGED]

    print(f"Zone: {DOMAIN}   ({len(current)} records total)\n")

    print(f"UNTOUCHED — outside the three managed pairs ({len(out_of_scope)}):")
    for r in sorted(out_of_scope, key=lambda x: (x.get("type", ""), x.get("name", ""))):
        print(fmt(r))

    print(f"\nCURRENT state of the managed pairs ({len(in_scope)}):")
    if not in_scope:
        print("    (none — apex and www are unset)")
    for r in sorted(in_scope, key=lambda x: (x.get("type", ""), x.get("name", ""))):
        print(fmt(r))

    print("\nDESIRED:")
    changes = []
    for (rtype, name), records in targets.items():
        have = sorted(
            r.get("data", "").rstrip(".")
            for r in current
            if r.get("type") == rtype and r.get("name") == name
        )
        want = sorted(r["data"].rstrip(".") for r in records)
        status = "already correct" if have == want else "WILL REPLACE"
        if have != want:
            changes.append((rtype, name, records))
        print(f"  {rtype}/{name}  [{status}]")
        for r in records:
            print(f"    {r['data']}  ttl={r['ttl']}")

    if not changes:
        print("\nZone already matches the target. Nothing to do.")
        return 0

    print(f"\n{len(changes)} pair(s) would be replaced. A PUT replaces every record "
          f"of that type+name, so GoDaddy's parking records for those pairs are "
          f"removed as part of the write.")

    if not args.apply:
        print("\nPLAN ONLY — nothing applied. Re-run with Apply checked.")
        return 0

    print("\nApplying.")
    for rtype, name, records in changes:
        resp = session.put(f"{BASE}/{DOMAIN}/records/{rtype}/{name}",
                           json=records, timeout=30)
        if not resp.ok:
            print(f"  FAILED {rtype}/{name}: {resp.status_code} {resp.text[:300]}")
            resp.raise_for_status()
        print(f"  wrote {rtype}/{name} ({len(records)} record(s))")

    print("\nApplied. Verify public resolution (propagation is usually minutes "
          "on a 600 TTL):")
    print(f"  dig +short {DOMAIN} A")
    print(f"  dig +short www.{DOMAIN} CNAME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
