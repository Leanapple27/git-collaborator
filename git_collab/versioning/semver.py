from __future__ import annotations
from dataclasses import dataclass
from git_collab.versioning.commit_parser import ConventionalCommit

@dataclass
class SemVer:
    """Represents a Semantic Version."""
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        """Return the string representation of the semantic version."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> SemVer:
        """Parse a version string like '1.2.3' or 'v1.2.3'."""
        v = version_str.lstrip('vV')
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid semantic version string: {version_str}")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))

    def bump_major(self) -> SemVer:
        """Bump the major version and reset minor/patch to 0."""
        return SemVer(self.major + 1, 0, 0)

    def bump_minor(self) -> SemVer:
        """Bump the minor version and reset patch to 0."""
        return SemVer(self.major, self.minor + 1, 0)

    def bump_patch(self) -> SemVer:
        """Bump the patch version."""
        return SemVer(self.major, self.minor, self.patch + 1)

@dataclass
class BumpDecision:
    """Contains the decision of how a version should be bumped based on commits."""
    current: SemVer
    recommended: SemVer
    bump_type: str  # 'major', 'minor', 'patch', 'none'
    reasons: list[str]

def calculate_bump(current_version: str, commits: list[ConventionalCommit]) -> BumpDecision:
    """Calculate the version bump based on a list of conventional commits."""
    current = SemVer.from_string(current_version)
    
    is_breaking = any(c.is_breaking for c in commits)
    is_feat = any(c.type == 'feat' for c in commits)
    is_fix = any(c.type == 'fix' for c in commits)
    
    reasons = []
    if is_breaking:
        reasons.append("Breaking changes detected.")
        recommended = current.bump_major()
        bump_type = 'major'
    elif is_feat:
        reasons.append("New features detected.")
        recommended = current.bump_minor()
        bump_type = 'minor'
    elif is_fix:
        reasons.append("Bug fixes detected.")
        recommended = current.bump_patch()
        bump_type = 'patch'
    else:
        reasons.append("No impactful changes detected.")
        recommended = current
        bump_type = 'none'
        
    return BumpDecision(
        current=current,
        recommended=recommended,
        bump_type=bump_type,
        reasons=reasons
    )
