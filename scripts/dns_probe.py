"""Probe which GoDaddy API surface this account actually has.

Diagnostic only. Prints status codes and short body snippets — never the token.
Delete once dns_sync.py is confirmed working against the right endpoint.
"""

import os
import sys

import requests

DOMAIN = "audit-agent.ca"
PAT = os.environ.get("GODADDY_PAT", "").strip()
if not PAT:
    sys.exit("GODADDY_PAT not set")

CANDIDATES = [
    ("v1 list domains", "GET", "https://api.godaddy.com/v1/domains"),
    ("v1 domain detail", "GET", f"https://api.godaddy.com/v1/domains/{DOMAIN}"),
    ("v1 records", "GET", f"https://api.godaddy.com/v1/domains/{DOMAIN}/records"),
    ("v1 records A", "GET", f"https://api.godaddy.com/v1/domains/{DOMAIN}/records/A"),
    ("v2 records", "GET", f"https://api.godaddy.com/v2/domains/{DOMAIN}/records"),
    ("v3 zones list", "GET", "https://api.godaddy.com/v3/domains/zones"),
    ("v3 zone records", "GET",
     f"https://api.godaddy.com/v3/domains/zones/{DOMAIN}/dns-records"),
]

# Both auth schemes: v1 historically used sso-key, current docs say Bearer PAT.
SCHEMES = {
    "Bearer": f"Bearer {PAT}",
    "sso-key": f"sso-key {PAT}",
}

for scheme_name, header_value in SCHEMES.items():
    print(f"\n{'=' * 60}\nAuth scheme: {scheme_name}\n{'=' * 60}")
    for label, method, url in CANDIDATES:
        try:
            resp = requests.request(
                method, url,
                headers={"Authorization": header_value, "Accept": "application/json"},
                timeout=30,
            )
        except Exception as exc:
            print(f"  {label:<20} ERROR {type(exc).__name__}")
            continue

        marker = "  <-- WORKS" if resp.status_code == 200 else ""
        print(f"  {label:<20} {resp.status_code}{marker}")

        if resp.status_code != 200:
            print(f"      {resp.text[:180]}".replace("\n", " "))
            continue

        # On success, show what the account actually contains. Domain names
        # are not secret; this is the whole point of the diagnostic.
        if label == "v1 list domains":
            try:
                domains = resp.json()
            except Exception:
                print(f"      {resp.text[:200]}")
                continue
            print(f"      {len(domains)} domain(s) in this account:")
            for d in domains:
                print(f"        {d.get('domain')}  status={d.get('status')} "
                      f"expires={str(d.get('expires'))[:10]}")
        else:
            print(f"      {resp.text[:200]}".replace("\n", " "))
