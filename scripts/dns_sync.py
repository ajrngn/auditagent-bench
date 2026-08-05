"""Point audit-agent.ca at GitHub Pages via the GoDaddy Domains API (v3).

Plans by default; applies only with --apply. Run from GitHub Actions, where the
token lives in Actions Secrets and never touches a laptop.

    GODADDY_PAT=... GITHUB_USER=... python scripts/dns_sync.py
    GODADDY_PAT=... GITHUB_USER=... python scripts/dns_sync.py --apply

Only three (name, type) pairs are managed: @/A, @/AAAA, www/CNAME. Everything
else in the zone — MX, TXT, anything carrying mail or verification — is
reported and left alone.

The v3 API has no bulk-replace endpoint, so changes are individual creates and
deletes.
"""

from __future__ import annotations

import argparse
import os
import sys

import requests

BASE = "https://api.godaddy.com/v3/domains"
DOMAIN = "audit-agent.ca"

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

# GoDaddy's v3 API rejects a TTL below 600.
TTL = 600

MANAGED = {("@", "A"), ("@", "AAAA"), ("www", "CNAME")}


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"error: {name} is not set")
    return value


def key(record: dict) -> tuple[str, str, str]:
    return (record["name"], record["type"], record["data"].rstrip("."))


def fmt(record: dict) -> str:
    return f"  {record['type']:<6} {record['name']:<8} {record['data']:<40} ttl={record.get('ttl')}"


def list_records(session: requests.Session) -> list[dict]:
    """Every record in the zone, paged."""
    records: list[dict] = []
    page = 1
    while True:
        resp = session.get(
            f"{BASE}/zones/{DOMAIN}/dns-records",
            params={"page": page, "pageSize": 100},
            timeout=30,
        )
        if resp.status_code == 401:
            sys.exit("error: GoDaddy rejected the token (401). It may be expired or lack DNS scope.")
        if resp.status_code == 403:
            sys.exit("error: token lacks permission for this domain (403).")
        resp.raise_for_status()

        items = resp.json().get("items", [])
        records.extend(items)
        if len(items) < 100:
            return records
        page += 1


def desired_records(github_user: str) -> list[dict]:
    return (
        [{"name": "@", "type": "A", "data": ip, "ttl": TTL} for ip in PAGES_A]
        + [{"name": "@", "type": "AAAA", "data": ip, "ttl": TTL} for ip in PAGES_AAAA]
        + [{"name": "www", "type": "CNAME", "data": f"{github_user}.github.io", "ttl": TTL}]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="apply the plan; without this the script only reports")
    args = parser.parse_args()

    pat = env("GODADDY_PAT")
    github_user = env("GITHUB_USER")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {pat}", "Accept": "application/json"})

    current = list_records(session)
    in_scope = [r for r in current if (r["name"], r["type"]) in MANAGED]
    out_of_scope = [r for r in current if (r["name"], r["type"]) not in MANAGED]

    desired = desired_records(github_user)
    desired_keys = {key(d) for d in desired}
    current_keys = {key(r) for r in in_scope}

    to_delete = [r for r in in_scope if key(r) not in desired_keys]
    to_create = [d for d in desired if key(d) not in current_keys]

    print(f"Zone: {DOMAIN}")
    print(f"CNAME target: {github_user}.github.io")
    print()
    print(f"Untouched ({len(out_of_scope)}) — outside the managed name/type pairs:")
    for r in sorted(out_of_scope, key=key):
        print(fmt(r))
    print()
    print(f"DELETE ({len(to_delete)}):")
    for r in sorted(to_delete, key=key):
        print(fmt(r))
    print()
    print(f"CREATE ({len(to_create)}):")
    for r in sorted(to_create, key=key):
        print(fmt(r))
    print()
    print(f"Already correct: {len(in_scope) - len(to_delete)}")

    if not to_delete and not to_create:
        print("\nZone already matches the target. Nothing to do.")
        return 0

    if not args.apply:
        print("\nPlan only — nothing applied. Re-run with --apply to make these changes.")
        return 0

    print("\nApplying.")

    # Deletes first, so a replaced apex record does not collide with its successor.
    for record in to_delete:
        resp = session.delete(
            f"{BASE}/zones/{DOMAIN}/dns-records/{record['recordId']}", timeout=30
        )
        if resp.status_code == 409:
            # SOA and NS are GoDaddy-managed and cannot be removed.
            print(f"  skip   {record['type']:<6} {record['name']:<8} {record['data']} (managed)")
            continue
        resp.raise_for_status()
        print(f"  delete {record['type']:<6} {record['name']:<8} {record['data']}")

    for record in to_create:
        resp = session.post(f"{BASE}/zones/{DOMAIN}/dns-records", json=record, timeout=30)
        resp.raise_for_status()
        print(f"  create {record['type']:<6} {record['name']:<8} {record['data']}")

    print("\nApplied. Verify public resolution:")
    print(f"  dig +short {DOMAIN} A")
    print(f"  dig +short www.{DOMAIN} CNAME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
