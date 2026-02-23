"""
Project management system inspired by OpenProject.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict
import sqlite3
import json
from pathlib import Path


@dataclass
class Project:
    """Represents a project."""
    id: str
    name: str
    identifier: str
    description: str = ""
    status: str = "active"  # active, archived, closed
    parent_id: Optional[str] = None
    members: List[str] = field(default_factory=list)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkPackage:
    """Represents a work package (task, bug, feature, etc)."""
    id: str
    project_id: str
    type: str  # task, bug, feature, milestone, epic
    subject: str
    description: str = ""
    status: str = "new"  # new, in_progress, review, closed, rejected, reopened
    priority: str = "normal"  # low, normal, high, urgent
    assignee: str = ""
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: float = 0
    spent_hours: float = 0
    progress_pct: int = 0
    parent_id: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Sprint:
    """Represents a sprint/iteration."""
    id: str
    project_id: str
    name: str
    goal: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "planning"  # planning, active, closed
    velocity: int = 0


class ProjectManager:
    """Core project management engine."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path.home() / ".blackroad" / "projects.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                identifier TEXT UNIQUE NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                parent_id TEXT,
                members TEXT,
                start_date TEXT,
                end_date TEXT,
                progress INTEGER DEFAULT 0,
                tags TEXT,
                created_at TEXT
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS work_packages (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                type TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'new',
                priority TEXT DEFAULT 'normal',
                assignee TEXT,
                start_date TEXT,
                due_date TEXT,
                estimated_hours REAL DEFAULT 0,
                spent_hours REAL DEFAULT 0,
                progress_pct INTEGER DEFAULT 0,
                parent_id TEXT,
                labels TEXT,
                created_at TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wp_id TEXT NOT NULL,
                user TEXT,
                hours REAL,
                activity TEXT,
                comment TEXT,
                logged_at TEXT,
                FOREIGN KEY(wp_id) REFERENCES work_packages(id)
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS sprints (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                goal TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'planning',
                velocity INTEGER DEFAULT 0,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS sprint_assignments (
                wp_id TEXT PRIMARY KEY,
                sprint_id TEXT NOT NULL,
                FOREIGN KEY(wp_id) REFERENCES work_packages(id),
                FOREIGN KEY(sprint_id) REFERENCES sprints(id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_project(self, name: str, identifier: str,
                      description: str = "", parent_id: Optional[str] = None) -> str:
        """Create a new project."""
        import uuid
        project_id = str(uuid.uuid4())[:8]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO projects
            (id, name, identifier, description, parent_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (project_id, name, identifier, description, parent_id,
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return project_id

    def create_work_package(self, project_id: str, wp_type: str, subject: str,
                           description: str = "", assignee: str = "",
                           priority: str = "normal", estimated_hours: float = 0,
                           labels: Optional[List[str]] = None) -> str:
        """Create a new work package."""
        import uuid
        wp_id = str(uuid.uuid4())[:8]
        labels = labels or []

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO work_packages
            (id, project_id, type, subject, description, assignee, priority,
             estimated_hours, labels, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (wp_id, project_id, wp_type, subject, description, assignee,
              priority, estimated_hours, json.dumps(labels),
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return wp_id

    def update_wp_status(self, wp_id: str, status: str) -> bool:
        """Update work package status."""
        valid_statuses = {"new", "in_progress", "review", "closed", "rejected", "reopened"}
        if status not in valid_statuses:
            return False

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE work_packages SET status = ? WHERE id = ?', (status, wp_id))
        conn.commit()
        conn.close()
        return True

    def log_time(self, wp_id: str, user: str, hours: float,
                activity: str, comment: str = "") -> bool:
        """Log time spent on a work package."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Add time log
        c.execute('''
            INSERT INTO time_logs (wp_id, user, hours, activity, comment, logged_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (wp_id, user, hours, activity, comment, datetime.now().isoformat()))

        # Update spent_hours
        c.execute('''
            SELECT COALESCE(SUM(hours), 0) FROM time_logs WHERE wp_id = ?
        ''', (wp_id,))
        total_spent = c.fetchone()[0]

        c.execute('UPDATE work_packages SET spent_hours = ? WHERE id = ?',
                 (total_spent, wp_id))

        conn.commit()
        conn.close()
        return True

    def create_sprint(self, project_id: str, name: str, goal: str,
                     start_date: date, end_date: date) -> str:
        """Create a sprint."""
        import uuid
        sprint_id = str(uuid.uuid4())[:8]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO sprints
            (id, project_id, name, goal, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sprint_id, project_id, name, goal, start_date.isoformat(),
              end_date.isoformat()))
        conn.commit()
        conn.close()
        return sprint_id

    def assign_to_sprint(self, wp_id: str, sprint_id: str) -> bool:
        """Assign a work package to a sprint."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                INSERT OR REPLACE INTO sprint_assignments (wp_id, sprint_id)
                VALUES (?, ?)
            ''', (wp_id, sprint_id))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def get_sprint_board(self, sprint_id: str) -> Dict[str, List[Dict]]:
        """Get work packages in a sprint grouped by status."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT wp.id, wp.subject, wp.status, wp.priority, wp.assignee
            FROM work_packages wp
            JOIN sprint_assignments sa ON wp.id = sa.wp_id
            WHERE sa.sprint_id = ?
            ORDER BY wp.status, wp.priority DESC
        ''', (sprint_id,))

        rows = c.fetchall()
        conn.close()

        board = {}
        for wp_id, subject, status, priority, assignee in rows:
            if status not in board:
                board[status] = []
            board[status].append({
                "id": wp_id,
                "subject": subject,
                "priority": priority,
                "assignee": assignee
            })

        return board

    def get_project_stats(self, project_id: str) -> Dict:
        """Get project statistics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT COUNT(*), status FROM work_packages
            WHERE project_id = ?
            GROUP BY status
        ''', (project_id,))

        stats = {
            "open": 0,
            "closed": 0,
            "progress": 0
        }

        for count, status in c.fetchall():
            if status in {"closed"}:
                stats["closed"] += count
            else:
                stats["open"] += count

        c.execute('''
            SELECT COALESCE(SUM(progress_pct), 0) / COUNT(*), COUNT(*)
            FROM work_packages WHERE project_id = ?
        ''', (project_id,))

        avg_progress, count = c.fetchone()
        stats["progress"] = int(avg_progress) if count > 0 else 0

        conn.close()
        return stats

    def get_burndown(self, sprint_id: str) -> List[Dict]:
        """Get burndown chart data (points remaining per day)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT COALESCE(SUM(estimated_hours), 0) FROM work_packages wp
            JOIN sprint_assignments sa ON wp.id = sa.wp_id
            WHERE sa.sprint_id = ? AND wp.status NOT IN ('closed', 'rejected')
        ''', (sprint_id,))

        remaining = c.fetchone()[0]
        conn.close()

        # Simple linear burndown (stub)
        return [{"day": 0, "remaining": remaining}]

    def get_roadmap(self, project_id: str) -> List[Dict]:
        """Get project roadmap (epics with progress)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT id, subject, progress_pct, due_date FROM work_packages
            WHERE project_id = ? AND type = 'epic'
            ORDER BY due_date
        ''', (project_id,))

        epics = []
        for epic_id, subject, progress, due_date in c.fetchall():
            epics.append({
                "id": epic_id,
                "subject": subject,
                "progress": progress,
                "due_date": due_date
            })

        conn.close()
        return epics

    def search(self, query: str, project_id: Optional[str] = None) -> List[Dict]:
        """Full-text search on work package titles and descriptions."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        search_term = f"%{query}%"
        if project_id:
            c.execute('''
                SELECT id, subject, type, status FROM work_packages
                WHERE (subject LIKE ? OR description LIKE ?)
                AND project_id = ?
            ''', (search_term, search_term, project_id))
        else:
            c.execute('''
                SELECT id, subject, type, status FROM work_packages
                WHERE subject LIKE ? OR description LIKE ?
            ''', (search_term, search_term))

        results = []
        for wp_id, subject, wp_type, status in c.fetchall():
            results.append({
                "id": wp_id,
                "subject": subject,
                "type": wp_type,
                "status": status
            })

        conn.close()
        return results


# CLI interface
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Project management system")
    subparsers = parser.add_subparsers(dest="command")

    # projects command
    projects_parser = subparsers.add_parser("projects")

    # create-wp command
    cwp_parser = subparsers.add_parser("create-wp")
    cwp_parser.add_argument("project_id")
    cwp_parser.add_argument("type")
    cwp_parser.add_argument("subject")
    cwp_parser.add_argument("--assignee", default="")

    # sprint-board command
    sprint_parser = subparsers.add_parser("sprint-board")
    sprint_parser.add_argument("sprint_id")

    args = parser.parse_args()
    pm = ProjectManager()

    if args.command == "projects":
        conn = sqlite3.connect(pm.db_path)
        c = conn.cursor()
        c.execute('SELECT id, name, status FROM projects')
        for pid, name, status in c.fetchall():
            print(f"{name} ({pid}): {status}")
        conn.close()
    elif args.command == "create-wp":
        wp_id = pm.create_work_package(args.project_id, args.type, args.subject,
                                       assignee=args.assignee)
        print(f"Work package created: {wp_id}")
    elif args.command == "sprint-board":
        board = pm.get_sprint_board(args.sprint_id)
        for status, wps in board.items():
            print(f"\n{status.upper()}:")
            for wp in wps:
                print(f"  [{wp['priority']}] {wp['subject']} -> {wp['assignee']}")
