from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class ConventionalCommit:
    """Represents a parsed conventional commit."""
    type: str
    scope: str | None
    description: str
    is_breaking: bool
    raw_message: str

def parse_commit(message: str) -> ConventionalCommit | None:
    """
    Parse a single commit message into a ConventionalCommit.
    Returns None if the message does not follow the specification.
    """
    pattern = r'^([a-zA-Z]+)(?:\(([^)]+)\))?(!)?:\s+(.*)'
    lines = message.strip().split('\n')
    header = lines[0]
    
    match = re.match(pattern, header)
    if not match:
        return None
        
    c_type, scope, bang, description = match.groups()
    is_breaking = bool(bang)
    
    if not is_breaking and len(lines) > 1:
        for line in lines[1:]:
            if line.startswith('BREAKING CHANGE:') or line.startswith('BREAKING-CHANGE:'):
                is_breaking = True
                break
                
    return ConventionalCommit(
        type=c_type.lower(),
        scope=scope.strip() if scope else None,
        description=description.strip(),
        is_breaking=is_breaking,
        raw_message=message
    )

def parse_commits(messages: list[str]) -> list[ConventionalCommit]:
    """Parse a list of commit messages, skipping invalid ones."""
    commits = []
    for msg in messages:
        commit = parse_commit(msg)
        if commit:
            commits.append(commit)
    return commits

def categorize_commits(commits: list[ConventionalCommit]) -> dict[str, list[ConventionalCommit]]:
    """Group commits into categories: features, fixes, breaking, other."""
    categories: dict[str, list[ConventionalCommit]] = {
        'features': [],
        'fixes': [],
        'breaking': [],
        'other': []
    }
    
    for commit in commits:
        if commit.is_breaking:
            categories['breaking'].append(commit)
        elif commit.type == 'feat':
            categories['features'].append(commit)
        elif commit.type == 'fix':
            categories['fixes'].append(commit)
        else:
            categories['other'].append(commit)
            
    return categories
