# Contributing to FPMS

Thank you for your interest in contributing to the Fuel Pump Management System (FPMS)! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork into your bench:

   ```bash
   cd $PATH_TO_YOUR_BENCH
   bench get-app https://github.com/<your-username>/fpms --branch version-16
   bench --site your-site.com install-app fpms
   ```

3. **Add the upstream remote:**

   ```bash
   cd apps/fpms
   git remote add upstream https://github.com/kodlyft/fpms.git
   ```

4. **Create a new branch** from `version-16`:

   ```bash
   git checkout -b feat/your-feature-name version-16
   ```

## Development Setup

### Prerequisites

| Dependency       | Version  |
| ---------------- | -------- |
| Python           | >= 3.14  |
| Frappe Framework | v16      |
| ERPNext          | v16      |

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality before every commit:

```bash
cd apps/fpms
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### Backend Development

```bash
cd $PATH_TO_YOUR_BENCH
bench start       # Start Frappe development server
```

## Making Changes

- Keep changes focused. A single PR should address a single concern.
- Write or update tests for any new functionality.
- Ensure all linters and tests pass before submitting:

  ```bash
  # Python linting
  ruff check fpms/

  # All pre-commit hooks (ruff, semgrep, prettier)
  pre-commit run --all-files

  # Tests
  bench --site your-site.com run-tests --app fpms
  ```

## Commit Guidelines

All commits **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This enables automated versioning and changelog generation.

### Format

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Allowed Types

| Type       | Description                              |
| ---------- | ---------------------------------------- |
| `feat`     | A new feature                            |
| `fix`      | A bug fix                                |
| `docs`     | Documentation only changes               |
| `style`    | Formatting, missing semicolons, etc.     |
| `refactor` | Code change that neither fixes nor adds  |
| `perf`     | Performance improvement                  |
| `test`     | Adding or updating tests                 |
| `build`    | Build system or dependency changes       |
| `ci`       | CI configuration changes                 |
| `chore`    | Other changes that don't modify src/test |
| `revert`   | Reverts a previous commit                |

### Examples

```
feat: add dip-chart interpolation to Tank
fix: correct shift variance rounding on multi-nozzle reconciliation
docs: document OGRA fuel price notification workflow
refactor(pricing): simplify effective-dated Item Price lookup
test: add unit tests for wet-stock variance
```

## Pull Request Process

1. **Sync your branch** with the latest `version-16`:

   ```bash
   git fetch upstream
   git rebase upstream/version-16
   ```

2. **Push** your branch and open a Pull Request against the `version-16` branch.

3. Fill out the PR template completely — describe what changed and why.

4. Ensure all CI checks pass (linting, semgrep, tests).

5. A maintainer will review your PR. Address any feedback and push updates to the same branch.

6. Once approved, a maintainer will merge your PR.

## Reporting Bugs

Use the [Bug Report](https://github.com/kodlyft/fpms/issues/new?template=bug_report.md) issue template. Please include:

- Steps to reproduce
- Expected vs. actual behavior
- Screenshots or error logs if applicable
- Your environment (Frappe version, ERPNext version, OS)

## Requesting Features

Use the [Feature Request](https://github.com/kodlyft/fpms/issues/new?template=feature_request.md) issue template. Describe:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

---

Thank you for contributing to FPMS!
