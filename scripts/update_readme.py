import os
import sys
import re
import urllib.request
import json
from datetime import datetime

USERNAME = "adityashirsatrao007"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def fetch_merged_prs():
    url = f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr+is:merged&sort=created&order=desc&per_page=100"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching PRs: {e}", file=sys.stderr)
        sys.exit(1)

def format_date(iso_date_str):
    # e.g., "2025-07-29T18:30:00Z" -> "Jul 29, 2025"
    dt = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%b %d, %Y")

def main():
    print("Fetching merged PRs from GitHub API...")
    data = fetch_merged_prs()
    total_count = data.get("total_count", 0)
    items = data.get("items", [])
    
    unique_repos = set()
    unique_orgs = set()
    
    pr_rows = []
    for index, item in enumerate(items, 1):
        title = item.get("title", "")
        # Sanitize title to avoid markdown breaking
        title = title.replace("[", "\\[").replace("]", "\\]").replace("|", "\\|")
        html_url = item.get("html_url", "")
        repo_url = item.get("repository_url", "")
        repo_name = repo_url.split("/repos/")[-1] # e.g. "firstcontributions/first-contributions"
        unique_repos.add(repo_name)
        
        org_name = repo_name.split("/")[0]
        unique_orgs.add(org_name)
        
        # Format date
        merged_on = format_date(item.get("closed_at"))
        
        pr_rows.append(
            f"| {index} | [{title}]({html_url}) | [{repo_name}](https://github.com/{repo_name}) | {merged_on} |"
        )
        
    print(f"Found {total_count} merged PRs across {len(unique_repos)} repos and {len(unique_orgs)} orgs.")
    
    # Generate PR list section
    pr_list_content = f"""<details>
<summary><b>📂 Click to expand / collapse the full list of {total_count} merged pull requests</b></summary>
<br/>

| # | PR Title | Repository | Merged On |
|:-:|----------|------------|:---------:|
""" + "\n".join(pr_rows) + "\n\n</details>"

    # Generate Highlights section
    highlights_content = f"""<div align="center">
  <img src="https://img.shields.io/badge/Merged_PRs-{total_count}-6E40C9?style=for-the-badge&logo=git&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Unique_Repos-{len(unique_repos)}+-32C850?style=for-the-badge&logo=github&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Organizations-{len(unique_orgs)}+-007ACC?style=for-the-badge&logo=enterprise&logoColor=white" />
</div>"""

    # Read README.md
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("README.md not found!", file=sys.stderr)
        sys.exit(1)
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace PR list block
    pr_pattern = re.compile(
        r"<!-- START_PR_LIST -->.*?<!-- END_PR_LIST -->", 
        re.DOTALL
    )
    new_content = pr_pattern.sub(
        f"<!-- START_PR_LIST -->\n{pr_list_content}\n<!-- END_PR_LIST -->", 
        content
    )
    
    # Replace Highlights block
    highlights_pattern = re.compile(
        r"<!-- START_HIGHLIGHTS -->.*?<!-- END_HIGHLIGHTS -->", 
        re.DOTALL
    )
    new_content = highlights_pattern.sub(
        f"<!-- START_HIGHLIGHTS -->\n{highlights_content}\n<!-- END_HIGHLIGHTS -->", 
        new_content
    )
    
    # Write back to README.md
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("README.md updated successfully!")

if __name__ == "__main__":
    main()
