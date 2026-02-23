# BlackRoad OpenProject

Project management system inspired by OpenProject. Enables project planning, work package tracking, sprints, and resource management.

## Features

- **Projects & hierarchies**: Organize work into projects and sub-projects
- **Work packages**: Tasks, bugs, features, milestones, and epics with full lifecycle
- **Sprint planning**: Create sprints with goals and velocity tracking
- **Time tracking**: Log hours and track progress
- **Burndown charts**: Visualize sprint progress
- **Roadmap**: Epic-based project roadmap with progress visibility
- **Full-text search**: Search work packages by title and description
- **SQLite backend**: Persistent storage at `~/.blackroad/projects.db`

## Installation

```bash
python -m pip install --upgrade pip
```

## Usage

```bash
# List projects
python src/project_manager.py projects

# Create a work package
python src/project_manager.py create-wp PROJECT_ID task "Fix login bug" --assignee alice

# View sprint board
python src/project_manager.py sprint-board SPRINT_ID
```

## Database Schema

- `projects`: Project definitions and metadata
- `work_packages`: Tasks, bugs, features, epics
- `time_logs`: Time tracking entries
- `sprints`: Sprint planning and tracking
- `sprint_assignments`: WP-to-sprint associations
