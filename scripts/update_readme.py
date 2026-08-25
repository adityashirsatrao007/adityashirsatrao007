import os
import sys
import re
import urllib.request
import json
import time
from datetime import datetime

USERNAME = "adityashirsatrao007"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def fetch_all_merged_prs(per_page=100):
    """Fetch all merged PRs with pagination (GitHub Search caps at 1000 results)."""
    all_items = []
    total_count = None
    page = 1
    while True:
        url = f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr+is:merged&sort=created&order=desc&per_page={per_page}&page={page}"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        req.add_header("Accept", "application/vnd.github+json")
        if GITHUB_TOKEN:
            req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if total_count is None:
                    total_count = data.get("total_count", 0)
                items = data.get("items", [])
                all_items.extend(items)
                # Stop if fewer than per_page or reached total or API 1000 cap
                if len(items) < per_page or len(all_items) >= total_count or len(all_items) >= 1000:
                    break
                page += 1
                time.sleep(0.3)  # be kind to API
        except Exception as e:
            print(f"Error fetching PRs page {page}: {e}", file=sys.stderr)
            sys.exit(1)
    return total_count, all_items

def format_date(iso_date_str):
    dt = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%b %d, %Y")

def format_month_year(iso_date_str):
    dt = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%b %Y")

def main():
    print("Fetching merged PRs from GitHub API...")
    total_count, items = fetch_all_merged_prs()

    unique_repos = set()
    unique_orgs = set()
    dates = []

    pr_rows = []
    for index, item in enumerate(items, 1):
        title = item.get("title", "")
        title = title.replace("[", "\\[").replace("]", "\\]").replace("|", "\\|")
        html_url = item.get("html_url", "")
        repo_url = item.get("repository_url", "")
        repo_name = repo_url.split("/repos/")[-1]
        unique_repos.add(repo_name)
        org_name = repo_name.split("/")[0]
        unique_orgs.add(org_name)
        closed = item.get("closed_at")
        if closed:
            dates.append(closed)
        merged_on = format_date(closed) if closed else "—"
        pr_rows.append(
            f"| {index} | [{title}]({html_url}) | [{repo_name}](https://github.com/{repo_name}) | {merged_on} |"
        )

    print(f"Found {total_count} merged PRs across {len(unique_repos)} repos and {len(unique_orgs)} orgs.")

    pr_list_content = f"""<details>
<summary><b>📂 Click to expand / collapse the full list of {total_count} merged pull requests</b></summary>
<br/>

| # | PR Title | Repository | Merged On |
|:-:|----------|------------|:---------:|
""" + "\n".join(pr_rows) + "\n\n</details>"

    highlights_content = f"""<div align="center">
  <img src="https://img.shields.io/badge/Merged_PRs-{total_count}-6E40C9?style=for-the-badge&logo=git&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Unique_Repos-{len(unique_repos)}+-32C850?style=for-the-badge&logo=github&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Organizations-{len(unique_orgs)}+-007ACC?style=for-the-badge&logo=enterprise&logoColor=white" />
</div>"""

    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("README.md not found!", file=sys.stderr)
        sys.exit(1)

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pr_pattern = re.compile(r"<!-- START_PR_LIST -->.*?<!-- END_PR_LIST -->", re.DOTALL)
    new_content = pr_pattern.sub(f"<!-- START_PR_LIST -->\n{pr_list_content}\n<!-- END_PR_LIST -->", content)

    highlights_pattern = re.compile(r"<!-- START_HIGHLIGHTS -->.*?<!-- END_HIGHLIGHTS -->", re.DOTALL)
    new_content = highlights_pattern.sub(f"<!-- START_HIGHLIGHTS -->\n{highlights_content}\n<!-- END_HIGHLIGHTS -->", new_content)

    header_pattern = re.compile(r"## ✅ Merged Pull Requests — All Time \(\d+ PRs\)")
    new_content = header_pattern.sub(f"## ✅ Merged Pull Requests — All Time ({total_count} PRs)", new_content)

    # Dynamic date range + repo counts line (was hardcoded "Jul 2025 → May 2026 · Across 40+")
    if dates:
        dates_sorted = sorted(dates)
        start_my = format_month_year(dates_sorted[0])
        end_my = format_month_year(dates_sorted[-1])
        range_str = f"{start_my} → {end_my}" if start_my != end_my else start_my
    else:
        range_str = "—"
    meta_pattern = re.compile(r"> Complete verified history via GitHub Search API.*Across.*repositories.*")
    meta_replacement = f"> Complete verified history via GitHub Search API · From **{range_str}** · Across **{len(unique_repos)}+ repositories, {len(unique_orgs)}+ organizations**"
    new_content = meta_pattern.sub(meta_replacement, new_content)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md updated successfully!")

if __name__ == "__main__":
    main()
