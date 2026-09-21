from __future__ import annotations
import datetime
from git_collab.versioning.commit_parser import ConventionalCommit, categorize_commits

def generate_changelog(commits: list[ConventionalCommit], version: str, date: str | None = None) -> str:
    """Generate a Markdown changelog from a list of commits."""
    if date is None:
        date = datetime.date.today().isoformat()
        
    categories = categorize_commits(commits)
    
    version_str = version if version.startswith('v') else f"v{version}"
    changelog = [f"## {version_str} ({date})\n"]
    
    if categories['breaking']:
        changelog.append("### [!] Breaking Changes")
        for commit in categories['breaking']:
            scope_str = f" ({commit.scope})" if commit.scope else ""
            changelog.append(f"- {commit.description}{scope_str}")
        changelog.append("")
        
    if categories['features']:
        changelog.append("### [+] Features")
        for commit in categories['features']:
            scope_str = f" ({commit.scope})" if commit.scope else ""
            changelog.append(f"- {commit.description}{scope_str}")
        changelog.append("")
        
    if categories['fixes']:
        changelog.append("### [*] Bug Fixes")
        for commit in categories['fixes']:
            scope_str = f" ({commit.scope})" if commit.scope else ""
            changelog.append(f"- {commit.description}{scope_str}")
        changelog.append("")
        
    if categories['other']:
        changelog.append("### [-] Other")
        for commit in categories['other']:
            scope_str = f" ({commit.scope})" if commit.scope else ""
            changelog.append(f"- {commit.description}{scope_str}")
        changelog.append("")
        
    return "\n".join(changelog).strip() + "\n"
