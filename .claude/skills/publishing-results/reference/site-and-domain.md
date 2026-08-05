# Site and domain reference — auditagent.ca

## Contents

- Site structure and what each page is for
- Publishing to GitHub Pages
- GoDaddy DNS records (apex + www)
- Verification steps
- If GitHub Pages is swapped for Cloud Storage

## Site structure

```
site/
├── index.html        # What the benchmark is, why it exists, links to repo + dataset
├── results.html      # Leaderboard table, generated from results/<run_id>/scored.jsonl
├── methodology.html  # Task definitions, label provenance, contamination policy
├── CNAME             # Contains exactly: auditagent.ca
└── assets/
    └── style.css
```

Static HTML only — no build step. The site must be publishable from a browser-only machine, so nothing here may require npm, a bundler, or a local server to render.

`results.html` is **generated**, never hand-edited. `06_analysis` writes it from scored run outputs so a published number cannot drift from its manifest. Regenerating it is part of cutting a results version.

## Publishing to GitHub Pages

1. Repo settings → Pages → Source: Deploy from a branch.
2. Branch `main`, folder `/site` (or move `site/` contents to a `gh-pages` branch).
3. Custom domain: `auditagent.ca`. This creates/expects `site/CNAME`.
4. Tick **Enforce HTTPS** once the certificate provisions (can take up to 24h after DNS resolves).

The `CNAME` file must contain the bare domain, one line, no protocol, no trailing slash.

## GoDaddy DNS records

Preferred path is the **DNS sync workflow**: Actions tab → "DNS sync" → Run workflow, leaving *Apply* unchecked to read the plan, then again with it checked. The token lives in Actions Secrets as `GODADDY_PAT` and never leaves the runner. Logic is in `scripts/dns_sync.py`; the CNAME target is derived from `github.repository_owner`.

The GoDaddy web UI works too and needs no credential at all — reasonable for a one-time setup. `notebooks/90_dns_setup.ipynb` is the same logic for Colab, and is redundant now that the workflow exists.

The v3 API has **no bulk-replace endpoint** — changes are individual `POST` creates and `DELETE`s by `recordId`, authenticated with `Authorization: Bearer <PAT>` against `https://api.godaddy.com/v3/domains`. The older `sso-key KEY:SECRET` scheme is retired; a tutorial using it will fail.

In GoDaddy: My Products → auditagent.ca → DNS → Manage Zones.

**Delete the GoDaddy parking records first** — the default `A @ → Parked` record and any `CNAME www → @` pointing at GoDaddy's forwarding will otherwise conflict.

Apex (`@`) — four A records, all four required:

| Type | Name | Value | TTL |
|---|---|---|---|
| A | @ | 185.199.108.153 | 600 |
| A | @ | 185.199.109.153 | 600 |
| A | @ | 185.199.110.153 | 600 |
| A | @ | 185.199.111.153 | 600 |

IPv6 (recommended, all four):

| Type | Name | Value | TTL |
|---|---|---|---|
| AAAA | @ | 2606:50c0:8000::153 | 600 |
| AAAA | @ | 2606:50c0:8001::153 | 600 |
| AAAA | @ | 2606:50c0:8002::153 | 600 |
| AAAA | @ | 2606:50c0:8003::153 | 600 |

Subdomain:

| Type | Name | Value | TTL |
|---|---|---|---|
| CNAME | www | `<github-username>.github.io` | 600 |

The CNAME target excludes the repository name — it is the user/org Pages host, not the project URL.

> These IPs are GitHub's published Pages addresses. Re-check GitHub's "Managing a custom domain" doc before a first setup; they change rarely but they do change.

## Verification

```powershell
Resolve-DnsName auditagent.ca -Type A
Resolve-DnsName www.auditagent.ca -Type CNAME
```

Expect the four A records and the `.github.io` target. Propagation is usually minutes on a 600 TTL but GoDaddy can take an hour. Do not re-edit records while waiting — repeated changes extend propagation.

Then confirm in GitHub repo settings that the domain shows a green check, and that Enforce HTTPS is available.

## If Cloud Storage is used instead

GCS static hosting cannot terminate HTTPS on a custom domain by itself; it needs an external HTTPS load balancer with a Google-managed certificate, and the DNS record becomes a single A record pointing at the load balancer's reserved static IP. That is more moving parts and more cost than this project needs. Prefer GitHub Pages unless the site starts serving the dataset itself.
