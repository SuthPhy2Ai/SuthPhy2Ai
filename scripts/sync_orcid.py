#!/usr/bin/env python3
"""
Automatically fetch Tianhao Su's publications from the public ORCID v3.0 API
and update the <!-- ORCID-PUBS:START --> ... <!-- ORCID-PUBS:END --> block in README.md.
Zero third-party dependencies (uses Python standard library only).
"""

from __future__ import annotations
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ORCID_ID = "0000-0003-3092-2535"
ORCID_API_URL = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
FEATURED_COUNT = 8


def fetch_orcid_works(retries: int = 3) -> dict:
    headers = {
        "Accept": "application/json",
        "User-Agent": "SuthPhy2Ai-GitHub-Profile-Sync/1.0 (https://github.com/SuthPhy2Ai)",
    }
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(ORCID_API_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_err = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch ORCID works after {retries} attempts: {last_err}")


def clean_title(raw_title: str) -> str:
    txt = html.unescape(raw_title or "").strip()
    # Attach <sub>/<sup> tightly to the preceding symbol and fuse split chemical formulas like H<sub>x</sub> CrO<sub>2</sub>
    txt = re.sub(r"\s*<(sub|sup)>\s*", r"<\1>", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s*</(sub|sup)>", r"</\1>", txt, flags=re.IGNORECASE)
    txt = re.sub(r"</(sub|sup)>\s+(?=[A-Z][a-z0-9<])", r"</\1>", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def norm_key(title: str) -> str:
    no_tags = re.sub(r"<[^>]+>", "", title)
    return re.sub(r"[^a-z0-9]+", "", no_tags.lower())


def parse_works(data: dict) -> list[dict]:
    groups = data.get("group", [])
    by_key: dict[str, dict] = {}

    for grp in groups:
        summaries = grp.get("work-summary") or []
        if not summaries:
            continue
        ws = summaries[0]
        raw_t = ((ws.get("title") or {}).get("title") or {}).get("value") or ""
        title = clean_title(raw_t)
        if not title:
            continue

        journal_raw = (ws.get("journal-title") or {}).get("value") or ""
        journal = html.unescape(journal_raw).strip()

        pdate = ws.get("publication-date") or {}
        year = int(((pdate.get("year") or {}).get("value")) or 0)
        month_raw = ((pdate.get("month") or {}).get("value")) or "0"
        month = int(month_raw) if month_raw.isdigit() else 0

        doi = ""
        ext_ids = ((ws.get("external-ids") or {}).get("external-id")) or []
        for eid in ext_ids:
            if (eid.get("external-id-type") or "").lower() == "doi":
                doi = (eid.get("external-id-value") or "").strip()
                break

        is_preprint = (not journal) or ("ssrn" in doi.lower())
        entry = {
            "title": title,
            "journal": journal or "Preprint",
            "year": year,
            "month": month,
            "doi": doi,
            "is_preprint": is_preprint,
        }

        key = norm_key(title)
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = entry
        else:
            # Prefer peer-reviewed journal entry over preprint, or newer metadata
            if prev["is_preprint"] and not entry["is_preprint"]:
                by_key[key] = entry
            elif prev["is_preprint"] == entry["is_preprint"] and (entry["year"], entry["month"]) > (prev["year"], prev["month"]):
                by_key[key] = entry

    items = list(by_key.values())
    items.sort(key=lambda x: (x["year"], x["month"], not x["is_preprint"]), reverse=True)
    return items


def format_entry(item: dict) -> str:
    yr_str = f"{item['year']}.{item['month']:02d}" if item["month"] else f"{item['year']}"
    title_md = f"[**{item['title']}**](https://doi.org/{item['doi']})" if item["doi"] else f"**{item['title']}**"
    return f"- `{yr_str}` · {title_md} — *{item['journal']}*"


def build_markdown_block(items: list[dict]) -> str:
    featured = items[:FEATURED_COUNT]
    older = items[FEATURED_COUNT:]

    lines = [format_entry(it) for it in featured]
    if older:
        lines.append("")
        lines.append(
            f"<details>\n<summary><b>📚 View Earlier Publications ({len(older)} more · PRB, APL, IUCrJ, Mat. Des., JPCL, ...)</b></summary>\n"
        )
        for it in older:
            lines.append(format_entry(it))
        lines.append("\n</details>")

    lines.append("")
    lines.append(
        f"<sub>🔄 Auto-synced from <a href=\"https://orcid.org/{ORCID_ID}\">ORCID ({ORCID_ID})</a> · Total indexed works: <b>{len(items)}</b></sub>"
    )
    return "\n".join(lines)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    readme_path = repo_root / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")

    start_tag = "<!-- ORCID-PUBS:START -->"
    end_tag = "<!-- ORCID-PUBS:END -->"
    if start_tag not in readme_text or end_tag not in readme_text:
        raise RuntimeError(f"Markers {start_tag} / {end_tag} not found in {readme_path}")

    raw_data = fetch_orcid_works()
    works = parse_works(raw_data)
    md_block = build_markdown_block(works)

    pattern = re.compile(
        re.escape(start_tag) + r".*?" + re.escape(end_tag),
        flags=re.DOTALL,
    )
    updated = pattern.sub(f"{start_tag}\n{md_block}\n{end_tag}", readme_text)

    if updated != readme_text:
        readme_path.write_text(updated, encoding="utf-8")
        print(f"Updated README.md with {len(works)} publications from ORCID {ORCID_ID}.")
    else:
        print(f"README.md already up-to-date ({len(works)} publications).")


if __name__ == "__main__":
    main()
