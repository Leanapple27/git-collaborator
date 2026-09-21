# 🚀 git-collaborator — Group Presentation & Quickstart Guide

> **GitHub Repository:** [https://github.com/Leanapple27/git-collaborator](https://github.com/Leanapple27/git-collaborator)
> 
> **Project Summary:** An AST-aware Python Git collaboration and conflict resolution system that automatically merges independent imports and functions, detects cross-branch conflicts before merging, and automates SemVer release planning.

---

## ⚡ 1-Minute Quickstart (Run on your machine)

Open PowerShell / Terminal and run:

```bash
# 1. Clone the repo
git clone https://github.com/Leanapple27/git-collaborator.git
cd git-collaborator

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Run all tests (all 37 will pass)
python -m pytest tests/ -v
```

---

## 🎬 Live Demo Commands (For Presentation)

### Step 0: Setup Demo Repository
```bash
python demo_setup.py
cd demo-project
```

---

### Step 1: The Problem — Standard Git Fails on Overlapping Imports/Functions
```bash
# Merge feature-auth first (clean)
git merge feature-auth

# Try merging feature-payments with vanilla Git
git merge feature-payments
```
* **Result:** ❌ Standard Git fails with `CONFLICT (content): Merge conflict in calculator.py` and creates ugly `<<<<<<<` markers.
* **Abort the mess:**
  ```bash
  git merge --abort
  git reset --hard HEAD~1
  ```

---

### Step 2: The Solution — `git-collaborator` AST Smart Merge
```bash
# 1. Merge feature-auth
git merge feature-auth

# 2. Run AST smart merge for feature-payments
python -m git_collab.cli.main merge feature-payments
```
* **Result:** ✅ `[OK] Merge complete! Conflicts: 0`. The AST engine automatically merged and sorted `OrderedDict` & `defaultdict` imports and added both functions cleanly without manual intervention!

---

### Step 3: Proactive Cross-Branch Conflict Warning
```bash
python -m git_collab.cli.main check
```
* **Result:** ⚡ Displays a cross-branch collision risk matrix without performing any merges. Flags `feature-tax-v1` vs `feature-tax-v2` as **🔴 `[HIGH]`** risk because both touch `calculate_tax()`.

---

### Step 4: True Conflict Detection (Honest Flagging)
```bash
git merge feature-tax-v1
python -m git_collab.cli.main merge feature-tax-v2 --dry-run
```
* **Result:** 🔍 Flags `[X] True conflicts: calculate_tax`. Demonstrates that the system safely identifies real semantic conflicts rather than blindly overwriting logic.
* **Reset:**
  ```bash
  git reset --hard v1.0.0
  ```

---

### Step 5: Automated SemVer Versioning & Changelog Generation
```bash
python -m git_collab.cli.main release plan
```
* **Result:** 📦 Scans Conventional Commits (`feat!:`, `fix:`, `feat:`), detects a breaking change, recommends a **`MAJOR`** version bump (`1.0.0` → `2.0.0`), and synthesizes structured release notes!

---

### Step 6: Team Branch Health Dashboard
```bash
python -m git_collab.cli.main branch
```
* **Result:** 📊 Live table showing branch staleness, divergence from main, and commit health.

---

## 🧠 Viva & Teacher Questions (Cheat Sheet)

| Question | Answer |
|---|---|
| **What parser did you use?** | Python's built-in `ast` module. It parses source code into an Abstract Syntax Tree to extract and manipulate functions, classes, and imports. |
| **How does 3-way merge work?** | It inspects three states: **BASE** (common ancestor found via `git merge-base`), **OURS** (current branch), and **THEIRS** (incoming branch). |
| **Why is this better than basic Git?** | Standard Git diffs raw text lines. `git-collaborator` diffs AST nodes, so independent imports and functions never trigger false conflicts. |
| **What libraries are used?** | `typer` (CLI), `rich` (terminal formatting), `textual` (TUI), and `gitpython` (Git plumbing). |
