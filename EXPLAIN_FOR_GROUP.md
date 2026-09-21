# 🎓 Group Presentation Guide (Simple & Clear)

> **Goal:** Help every team member understand the code, answer any professor question, and explain their part confidently in under 2 minutes.

---

## 🏗️ The Big Picture: Why We Built This

```
Vanilla Git:  Reads lines of plain text  --> False conflicts everywhere ❌
Our Project:  Reads Python AST structure --> Merges cleanly & warns early ✅
```

* **What is AST?**  
  AST stands for **Abstract Syntax Tree**. It is Python's built-in way of turning code text into a tree of objects (Imports, Functions, Classes).
* **Why does that matter?**  
  Standard Git thinks line 5 and line 6 overlapping is a conflict. Our tool looks at the tree and says: *"Hey, line 5 is `import os` and line 6 is `import json` — these are two independent imports, so we can keep both!"*

---

## 👥 Member Breakdown & Speaking Script

---

### 👤 Member 1: Project Intro & The Problem
**Files to Know:** `README.md`, `calculator.py`

#### What to Say:
1. *"Good morning/afternoon. Our project is **`git-collaborator`**, an AST-aware collaboration and conflict resolution system for Python."*
2. *"When developers work in teams, they create separate Git branches. When they merge, standard Git compares files line-by-line."*
3. *"If Developer A adds an import at the top of the file, and Developer B also adds an import at the top, standard Git crashes with a merge conflict."*
4. *"Let me demonstrate Git failing right now..."*

#### Demo Action:
```bash
git merge feature-auth
git merge feature-payments
# (Show the conflict markers in calculator.py)
git merge --abort
git reset --hard HEAD~1
```

#### Viva Question for Member 1:
* **Q: Why does standard Git create this conflict?**
* **A:** *"Because Git uses line-based diff algorithms (like Myers Diff). It doesn't know Python syntax — it only sees two people editing the same line numbers."*

---

### 👤 Member 2: AST Smart Merge Engine
**Files to Know:** `git_collab/semantic/ast_parser.py`, `git_collab/semantic/import_merger.py`, `git_collab/semantic/function_merger.py`

#### What to Say:
1. *"To fix this, we created a semantic merge engine using Python's standard `ast` module."*
2. *"Our algorithm does 3 simple steps:*
   - **Step 1:** Parse BASE, OURS, and THEIRS files into syntax trees using `ast.parse()`.
   - **Step 2 (Imports):** Take the mathematical union of all imported modules, remove duplicates, and sort them per PEP8.
   - **Step 3 (Functions):** Group code by function name. If Branch A added `func_a()` and Branch B added `func_b()`, combine both without conflicts."*
3. *"Let's run the exact same merge with our tool..."*

#### Demo Action:
```bash
git merge feature-auth
python -m git_collab.cli.main merge feature-payments
# (Show [OK] Merge complete! 0 conflicts)
```

#### Viva Question for Member 2:
* **Q: What happens if both developers change the exact same function with different logic?**
* **A:** *"Our tool detects that the AST node for the same function name has conflicting source code. It honestly flags it as a `[HIGH]` true conflict so developers can review it, rather than corrupting the code."*

---

### 👤 Member 3: Proactive Conflict Detection
**Files to Know:** `git_collab/semantic/conflict_detector.py`, `git_collab/cli/check_cmd.py`

#### What to Say:
1. *"In active teams, multiple branches exist at the same time. Developers usually only discover conflicts days later when they try to merge."*
2. *"We built an early-warning system with `gc check`."*
3. *"It scans all open branches, finds their common ancestor with `main` using `git merge-base`, and checks which Python functions each branch modified."*
4. *"If two branches touched the same function, it prints a risk table before anyone even attempts a merge."*

#### Demo Action:
```bash
python -m git_collab.cli.main check
```

#### Viva Question for Member 3:
* **Q: What are the risk levels in the table?**
* **A:**
  - **HIGH (🔴):** Both branches modified the *same function/class* (will conflict).
  - **MEDIUM (🟡):** Both branches touched the *same file*, but different functions (our tool will auto-resolve).
  - **LOW (🟢):** Branches touched separate files.

---

### 👤 Member 4: Automated Version Management (SemVer)
**Files to Know:** `git_collab/versioning/commit_parser.py`, `git_collab/versioning/semver.py`, `git_collab/versioning/changelog.py`

#### What to Say:
1. *"After resolving code and preparing a release, developers struggle to decide the next version number."*
2. *"Our system automates Semantic Versioning using the **Conventional Commits** standard."*
3. *"It reads commit messages since the last release tag:*
   - `fix:` -> Automatically triggers a **PATCH** bump (1.0.0 -> 1.0.1)
   - `feat:` -> Automatically triggers a **MINOR** bump (1.0.0 -> 1.1.0)
   - `feat!:` or `BREAKING CHANGE:` -> Automatically triggers a **MAJOR** bump (1.0.0 -> 2.0.0)"*
4. *"It also generates a clean Markdown changelog categorized into Breaking Changes, Features, and Bug Fixes."*

#### Demo Action:
```bash
python -m git_collab.cli.main release plan
```

#### Viva Question for Member 4:
* **Q: What is Semantic Versioning (SemVer)?**
* **A:** *"SemVer is a 3-part version numbering system: `MAJOR.MINOR.PATCH`. Major is for breaking changes, Minor is for new backward-compatible features, and Patch is for bug fixes."*

---

## 🛠️ Summary Table (The Whole Project in 4 Lines)

| Component | What it does | How it works |
|---|---|---|
| `gc merge <branch>` | Smart auto-merge | AST parsing -> union imports + combine independent functions |
| `gc check` | Early conflict warning | Checks if two branches modified the same AST symbol |
| `gc release plan` | Automated version bump | Reads Conventional Commits -> calculates SemVer + Changelog |
| `pytest tests/` | Verification suite | 37 automated unit and integration tests |
