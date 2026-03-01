# BlackRoad OpenProject

[![CI](https://github.com/BlackRoad-OS/blackroad-os-openproject/actions/workflows/ci.yml/badge.svg)](https://github.com/BlackRoad-OS/blackroad-os-openproject/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![npm compatible](https://img.shields.io/badge/npm-compatible-brightgreen.svg)](https://www.npmjs.com/)
[![Stripe Ready](https://img.shields.io/badge/Stripe-Ready-blueviolet.svg)](https://stripe.com)

> **BlackRoad OpenProject** is a production-grade, open-source project management platform — purpose-built for engineering teams who need full control over their project lifecycle, sprint cadence, and resource allocation. Inspired by OpenProject, redesigned for the BlackRoad OS ecosystem.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Requirements](#requirements)
5. [Installation](#installation)
   - [Python (pip)](#python-pip)
   - [JavaScript / Node.js (npm)](#javascript--nodejs-npm)
6. [Configuration](#configuration)
7. [Stripe Integration](#stripe-integration)
8. [Usage](#usage)
   - [CLI Reference](#cli-reference)
   - [Python API](#python-api)
9. [Database Schema](#database-schema)
10. [End-to-End Testing](#end-to-end-testing)
11. [CI/CD](#cicd)
12. [Contributing](#contributing)
13. [License](#license)

---

## Overview

BlackRoad OpenProject delivers a self-hosted project management experience with first-class support for:

- **Work package tracking** across all standard types (tasks, bugs, features, milestones, epics)
- **Sprint planning** with velocity measurement and burndown visualisation
- **Time tracking** with per-user activity logging
- **Roadmap views** driven by epic progress
- **Full-text search** across all work package subjects and descriptions
- **Stripe-powered billing** for SaaS deployments (seat-based or usage-based plans)

All project data is stored in a portable SQLite database, making it trivially deployable on any server, container, or developer laptop without external infrastructure dependencies.

---

## Features

| Feature | Description |
|---|---|
| Projects & hierarchies | Organise work into projects and unlimited sub-projects |
| Work packages | Tasks, bugs, features, milestones, and epics with full status lifecycle |
| Sprint planning | Create sprints with goals, start/end dates, and velocity tracking |
| Time tracking | Log hours per user per activity; totals are computed automatically |
| Burndown charts | Visualise remaining effort over a sprint timeline |
| Roadmap | Epic-based project roadmap with per-epic progress percentages |
| Full-text search | Search work packages by title and description, optionally scoped to a project |
| Stripe billing | Seat-based or usage-based subscription management via Stripe |
| SQLite backend | Persistent, zero-dependency storage at `~/.blackroad/projects.db` |
| CLI interface | Full-featured command-line interface for all core operations |

---

## Architecture

```
blackroad-os-openproject/
├── src/
│   └── project_manager.py   # Core engine, data models, CLI entry-point
├── tests/                   # pytest test suite
├── .github/
│   └── workflows/
│       └── ci.yml           # CI pipeline (lint → test → smoke)
├── LICENSE
└── README.md
```

**Data flow:**

```
CLI / API call
     │
     ▼
ProjectManager (Python class)
     │
     ▼
SQLite database (~/.blackroad/projects.db)
```

---

## Requirements

- **Python** 3.11 or newer
- **pip** 23+
- **Node.js** 18+ / **npm** 9+ *(required only for front-end tooling or npm package consumers)*
- A **Stripe** account with a valid API key *(required only for billing features)*

---

## Installation

### Python (pip)

```bash
# 1. Upgrade pip to the latest version
python -m pip install --upgrade pip

# 2. Install directly from the repository
pip install git+https://github.com/BlackRoad-OS/blackroad-os-openproject.git

# 3. Verify the installation
python -m project_manager --help
```

### JavaScript / Node.js (npm)

The BlackRoad OpenProject CLI and client bindings are published to the npm registry for JavaScript / TypeScript consumers and front-end tooling integration:

```bash
# Install globally
npm install -g blackroad-openproject

# Or add as a project dependency
npm install blackroad-openproject

# Verify
npx blackroad-openproject --version
```

> **Note:** The npm package shells out to the Python runtime under the hood. Ensure Python 3.11+ is available in your `PATH`.

---

## Configuration

All runtime configuration is supplied via environment variables:

| Variable | Default | Description |
|---|---|---|
| `BLACKROAD_DB_PATH` | `~/.blackroad/projects.db` | Absolute path to the SQLite database file |
| `STRIPE_SECRET_KEY` | *(none)* | Stripe secret key — required for billing features |
| `STRIPE_WEBHOOK_SECRET` | *(none)* | Stripe webhook signing secret |
| `STRIPE_PRICE_ID` | *(none)* | Default Stripe Price ID for new subscriptions |

Create a `.env` file in the project root (never commit this file):

```dotenv
BLACKROAD_DB_PATH=/var/blackroad/projects.db
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

---

## Stripe Integration

BlackRoad OpenProject supports **Stripe** for subscription billing in multi-user or SaaS deployments.

### Supported billing models

- **Seat-based** — charge per active team member per month
- **Usage-based** — charge per work package created or time logged

### Setup

1. Create a [Stripe](https://stripe.com) account and obtain your API keys from the [Stripe Dashboard](https://dashboard.stripe.com/apikeys).
2. Set the `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` environment variables (see [Configuration](#configuration)).
3. Configure a [Stripe webhook endpoint](https://dashboard.stripe.com/webhooks) pointing to `https://<your-domain>/webhooks/stripe`.
4. Set `STRIPE_PRICE_ID` to the Price ID of your subscription plan.

### Webhook events handled

| Event | Action |
|---|---|
| `checkout.session.completed` | Activate subscription, provision user seats |
| `invoice.paid` | Mark subscription as current, reset usage counters |
| `invoice.payment_failed` | Send payment failure notification, suspend access after grace period |
| `customer.subscription.deleted` | Deactivate subscription, revoke access |

> **Security:** Always verify the Stripe webhook signature using `STRIPE_WEBHOOK_SECRET` before processing any event payload.

---

## Usage

### CLI Reference

```bash
# List all projects
python src/project_manager.py projects

# Create a new project
python src/project_manager.py create-project "My Project" my-project --description "A sample project"

# Create a work package
python src/project_manager.py create-wp PROJECT_ID task "Fix login bug" --assignee alice

# View the sprint board for a sprint
python src/project_manager.py sprint-board SPRINT_ID

# Search work packages
python src/project_manager.py search "login" --project PROJECT_ID
```

Run `python src/project_manager.py --help` for a full list of commands and options.

### Python API

```python
from src.project_manager import ProjectManager

pm = ProjectManager()

# Create a project
project_id = pm.create_project("My Project", "my-project", description="A sample project")

# Create a work package
wp_id = pm.create_work_package(
    project_id=project_id,
    wp_type="task",
    subject="Fix login bug",
    assignee="alice",
    priority="high",
    estimated_hours=4.0,
)

# Update status
pm.update_wp_status(wp_id, "in_progress")

# Log time
pm.log_time(wp_id, user="alice", hours=2.5, activity="development")

# Create and populate a sprint
from datetime import date
sprint_id = pm.create_sprint(
    project_id, "Sprint 1", goal="Ship login fix",
    start_date=date(2026, 3, 1), end_date=date(2026, 3, 14)
)
pm.assign_to_sprint(wp_id, sprint_id)

# Retrieve sprint board
board = pm.get_sprint_board(sprint_id)

# Get project statistics
stats = pm.get_project_stats(project_id)

# Get roadmap epics
roadmap = pm.get_roadmap(project_id)

# Full-text search
results = pm.search("login", project_id=project_id)
```

---

## Database Schema

The SQLite database contains five tables:

### `projects`

| Column | Type | Description |
|---|---|---|
| `id` | TEXT PK | Short UUID identifier |
| `name` | TEXT | Human-readable project name |
| `identifier` | TEXT UNIQUE | URL-safe slug |
| `description` | TEXT | Optional project description |
| `status` | TEXT | `active` \| `archived` \| `closed` |
| `parent_id` | TEXT | Parent project ID (for sub-projects) |
| `members` | TEXT | JSON array of member usernames |
| `start_date` | TEXT | ISO 8601 date |
| `end_date` | TEXT | ISO 8601 date |
| `progress` | INTEGER | Overall progress percentage (0–100) |
| `tags` | TEXT | JSON array of tag strings |
| `created_at` | TEXT | ISO 8601 timestamp |

### `work_packages`

| Column | Type | Description |
|---|---|---|
| `id` | TEXT PK | Short UUID identifier |
| `project_id` | TEXT FK | Parent project |
| `type` | TEXT | `task` \| `bug` \| `feature` \| `milestone` \| `epic` |
| `subject` | TEXT | Work package title |
| `description` | TEXT | Detailed description |
| `status` | TEXT | `new` \| `in_progress` \| `review` \| `closed` \| `rejected` \| `reopened` |
| `priority` | TEXT | `low` \| `normal` \| `high` \| `urgent` |
| `assignee` | TEXT | Assigned user |
| `start_date` | TEXT | ISO 8601 date |
| `due_date` | TEXT | ISO 8601 date |
| `estimated_hours` | REAL | Estimated effort in hours |
| `spent_hours` | REAL | Total logged hours (auto-computed) |
| `progress_pct` | INTEGER | Completion percentage (0–100) |
| `parent_id` | TEXT | Parent work package (for subtasks) |
| `labels` | TEXT | JSON array of label strings |
| `created_at` | TEXT | ISO 8601 timestamp |

### `time_logs`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `wp_id` | TEXT FK | Work package |
| `user` | TEXT | Username |
| `hours` | REAL | Hours logged |
| `activity` | TEXT | Activity type (e.g. `development`, `testing`) |
| `comment` | TEXT | Optional note |
| `logged_at` | TEXT | ISO 8601 timestamp |

### `sprints`

| Column | Type | Description |
|---|---|---|
| `id` | TEXT PK | Short UUID identifier |
| `project_id` | TEXT FK | Parent project |
| `name` | TEXT | Sprint name |
| `goal` | TEXT | Sprint goal statement |
| `start_date` | TEXT | ISO 8601 date |
| `end_date` | TEXT | ISO 8601 date |
| `status` | TEXT | `planning` \| `active` \| `closed` |
| `velocity` | INTEGER | Planned velocity (story points / hours) |

### `sprint_assignments`

| Column | Type | Description |
|---|---|---|
| `wp_id` | TEXT PK/FK | Work package assigned to the sprint |
| `sprint_id` | TEXT FK | Sprint receiving the assignment |

---

## End-to-End Testing

The test suite lives in `tests/` and uses **pytest** with coverage reporting.

### Running tests locally

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run the full suite with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/test_project_manager.py -v
```

### Test coverage targets

| Module | Target coverage |
|---|---|
| `src/project_manager.py` | ≥ 90% |

### CI test execution

Tests run automatically on every push and pull request via the GitHub Actions workflow defined in `.github/workflows/ci.yml`. The pipeline executes the following stages in order:

1. **Lint** — `ruff check src/`
2. **Test** — `pytest tests/ -v --cov=src --cov-report=xml`
3. **Smoke** — `python src/project_manager.py --help`

All three stages must pass before a pull request can be merged.

---

## CI/CD

| Stage | Tool | Trigger |
|---|---|---|
| Lint | [ruff](https://github.com/astral-sh/ruff) | Push / PR |
| Unit & integration tests | pytest + pytest-cov | Push / PR |
| Smoke test | CLI `--help` | Push / PR |

View the latest pipeline status on the [Actions tab](https://github.com/BlackRoad-OS/blackroad-os-openproject/actions).

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes, ensuring all tests pass: `pytest tests/ -v`
3. Add or update tests to cover your changes (target ≥ 90% coverage).
4. Run the linter and fix any issues: `ruff check src/`
5. Open a pull request against `main` with a clear description of the change.

Please follow the existing code style and keep pull requests focused on a single concern.

---

## License

This project is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for the full text.
