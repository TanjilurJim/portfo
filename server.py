import os
import html
import json
import re
from functools import wraps
from email.message import EmailMessage
import smtplib
import ssl

from flask import Flask, flash, redirect, render_template, request, session, url_for
import sqlite3
import subprocess
from datetime import datetime, timezone, date
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.http import http_date

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "portfolio.db"
OWNER_NOTIFY_EMAIL = "tanjilurrahman21@gmail.com"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")


def _last_commit_datetime():
    """Latest git commit datetime (UTC). Fallback to server.py mtime."""
    try:
        ts = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ct'],
            cwd=BASE_DIR
        ).decode().strip()
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        try:
            ts = (BASE_DIR / 'server.py').stat().st_mtime
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None

@app.context_processor
def inject_last_modified():
    dt = _last_commit_datetime()
    formatted = dt.astimezone().strftime('%b %d, %Y %I:%M %p') if dt else ''
    return {
        'SITE_LAST_MODIFIED': formatted,
        'current_user': get_current_user(),
        'is_admin_user': is_admin_user(),
    }


def is_admin_user(user=None):
    user = user or get_current_user()
    return bool(user and user.get("username") == OWNER_NOTIFY_EMAIL)


def get_about_page_data():
    default_profile = {
        "hero_badge": "03 : About me",
        "hero_title": "A little about Jim",
        "hero_subtitle": "A clean story page with a bit of motion, a bit of personality, and enough structure to show who you are without feeling crowded.",
        "intro_label": "Who I am",
        "intro_heading": "Hello,",
        "intro_text": "I'm Tanjilur but you can call me Jim. I am a graduate of CSE dept from Brac University, I am an aspiring fullstack developer and I have explored machine learning through my thesis on multi-modal analysis of EEG and fMRI for sleep stage classification using deep learning.",
        "interests_label": "Interests & hobbies",
        "interests_text": "Outside academics, I love to travel. I'm passionate about music, playing bass, rapping, and writing poetry. A die-hard Liverpool fan, I also enjoy chess, watching football, and e-sports like Valorant, FIFA, RDR 2, Spiderman, and Fortnite. Check out my YouTube channel for more.",
        "focus_label": "Focus",
        "focus_text": "Full-stack development, clean UI, useful systems, and interactive experiences.",
        "current_label": "Currently into",
        "current_text": "Personal portfolio work, Flask apps, and motion-led storytelling on the web.",
        "resume_label": "Download My Resume",
        "resume_url": "./static/assets/Resume_of_Tanjilur_Rahman.pdf",
        "resume_filename": "Resume_of_Tanjilur_Rahman.pdf",
        "portrait_image": "./static/assets/images/2.jpg",
        "quick_role_label": "Role",
        "quick_role_value": "Full-stack enthusiast",
        "quick_home_label": "Home base",
        "quick_home_value": "Portfolio builder",
        "quick_note": "Scroll a little and the floating layers and image will drift subtly to create a soft parallax feel.",
        "timeline_title": "Timeline",
        "timeline_intro": "A few key beats from the path so far.",
        "skills_title": "Skills",
        "skills_intro": "A small horizontal strip of the tools and strengths that show up most often.",
        "projects_title": "Projects",
        "projects_intro": "Cards that can later be edited from the dashboard as the site grows.",
        "closing_title": "Could add next",
        "closing_text": "A skills strip, a featured projects band, a testimonial quote, or a \"now\" section. Those make About pages feel richer than a plain biography.",
    }

    default_social_links = [
        {"label": "GitHub", "icon_class": "fab fa-github", "url": "https://github.com/TanjilurJim", "sort_order": 1},
        {"label": "LinkedIn", "icon_class": "fab fa-linkedin-in", "url": "http://www.linkedin.com/in/tanjilur-rahman-jim", "sort_order": 2},
        {"label": "Facebook", "icon_class": "fab fa-facebook-f", "url": "https://www.facebook.com/RageAgainstJim/", "sort_order": 3},
        {"label": "Instagram", "icon_class": "fab fa-instagram", "url": "https://www.instagram.com/rage.against.jim", "sort_order": 4},
        {"label": "Twitter", "icon_class": "fab fa-twitter", "url": "https://twitter.com/4thSpiderman", "sort_order": 5},
    ]

    default_timeline = [
        {
            "title": "Brac University / CSE",
            "description": "Learned the structure behind software, built projects, and explored thesis work in EEG and fMRI analysis.",
            "icon_class": "fas fa-university",
            "sort_order": 1,
        },
        {
            "title": "Research focus",
            "description": "Worked with multi-modal analysis and deep learning to understand sleep stage classification better.",
            "icon_class": "fas fa-flask",
            "sort_order": 2,
        },
        {
            "title": "Building in public",
            "description": "Shaping a personal portfolio with Flask, SQLite, and practical dashboard tools instead of just a static resume.",
            "icon_class": "fas fa-pen-nib",
            "sort_order": 3,
        },
        {
            "title": "Next direction",
            "description": "More polished interfaces, more automation, and more pages that feel alive when you scroll through them.",
            "icon_class": "fas fa-arrow-right",
            "sort_order": 4,
        },
    ]

    default_skills = [
        {"title": "Python", "description": "Flask apps, data handling, scripting, and backend logic.", "accent": "sky", "badge": "PY", "icon_class": "fab fa-python", "sort_order": 1},
        {"title": "Django", "description": "Structured Python web development and admin-style patterns.", "accent": "emerald", "badge": "DJ", "icon_class": "fas fa-server", "sort_order": 2},
        {"title": "PHP", "description": "Legacy and practical server-side work across client projects.", "accent": "amber", "badge": "PHP", "icon_class": "fab fa-php", "sort_order": 3},
        {"title": "CodeIgniter", "description": "Lightweight PHP framework work for fast delivery.", "accent": "violet", "badge": "CI", "icon_class": "fas fa-bolt", "sort_order": 4},
        {"title": "Laravel", "description": "Robust backend APIs, Inertia stacks, and business tooling.", "accent": "rose", "badge": "LV", "icon_class": "fab fa-laravel", "sort_order": 5},
        {"title": "JavaScript", "description": "Frontend behavior, interfaces, and interactive UI logic.", "accent": "sky", "badge": "JS", "icon_class": "fab fa-js-square", "sort_order": 6},
        {"title": "React", "description": "Component-driven UI for modern app frontends.", "accent": "cyan", "badge": "RE", "icon_class": "fab fa-react", "sort_order": 7},
        {"title": "Next.js", "description": "Next-level React apps and app-router style web experiences.", "accent": "slate", "badge": "NX", "icon_class": "fas fa-layer-group", "sort_order": 8},
        {"title": "TypeScript", "description": "Safer frontend and backend code with typed structures.", "accent": "indigo", "badge": "TS", "icon_class": "fas fa-code", "sort_order": 9},
        {"title": "AWS", "description": "Deployment, hosting, and cloud-ready architecture.", "accent": "orange", "badge": "AWS", "icon_class": "fab fa-aws", "sort_order": 10},
        {"title": "GSAP", "description": "Motion-led storytelling, parallax, and cinematic entrances.", "accent": "pink", "badge": "GS", "icon_class": "fas fa-wand-magic-sparkles", "sort_order": 11},
        {"title": "Tailwind", "description": "Fast visual polish with responsive layouts and strong hierarchy.", "accent": "violet", "badge": "TW", "icon_class": "fas fa-wind", "sort_order": 12},
        {"title": "Machine Learning", "description": "Research exposure through EEG and fMRI sleep stage classification.", "accent": "amber", "badge": "ML", "icon_class": "fas fa-brain", "sort_order": 13},
    ]

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        profile_row = conn.execute("SELECT * FROM about_profile WHERE id = 1").fetchone()
        social_rows = conn.execute(
            "SELECT * FROM about_social_links WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
        ).fetchall()
        timeline_rows = conn.execute(
            "SELECT * FROM about_timeline WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
        ).fetchall()
        skill_rows = conn.execute(
            "SELECT * FROM about_skills WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
        ).fetchall()
        project_rows = conn.execute(
            "SELECT * FROM about_projects WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
        ).fetchall()

    profile = dict(profile_row) if profile_row else default_profile
    return {
        **profile,
        "social_links": [dict(row) for row in social_rows] or default_social_links,
        "timeline_items": [dict(row) for row in timeline_rows] or default_timeline,
        "skill_items": [dict(row) for row in skill_rows] or default_skills,
        "project_items": [normalize_project_row(dict(row)) for row in project_rows] or get_default_projects(),
    }


def slugify_text(value):
    slug = re.sub(r'[^a-z0-9]+', '-', (value or '').lower()).strip('-')
    return slug or 'project'


def static_asset_url(path_value):
    if not path_value:
        return ""
    path_value = str(path_value).strip()
    if path_value.startswith("./"):
        return "/" + path_value[2:]
    if path_value.startswith("/"):
        return path_value
    if path_value.startswith("static/"):
        return "/" + path_value
    return path_value


def get_default_projects():
    return [
        {
            "slug": "ricemill-erp",
            "number": "01",
            "title": "RiceMill ERP",
            "summary": "ERP software for rice mill operations with TypeScript, React, Laravel, and MySQL.",
            "description": "A business system built to manage rice mill workflows, operations, and records with a modern TypeScript and React frontend backed by Laravel and MySQL.",
            "stack": ["TypeScript", "React", "Laravel", "MySQL"],
            "live_url": "https://ricemillerp.com/",
            "login_url": "https://ricemillerp.com/login",
            "accent": "sky",
            "cover_image": "./static/assets/images/work001-01.jpg",
            "role": "Full-stack development",
            "outcome": "A tailored ERP experience with clean flows, structured data handling, and business-focused screens.",
            "link_label": "Case study",
            "link_url": "/works/ricemill-erp",
            "sort_order": 1,
            "is_active": 1,
        },
        {
            "slug": "unisalesbd",
            "number": "02",
            "title": "UniSalesBD",
            "summary": "Laravel and jQuery-based business site for sales operations and presentation.",
            "description": "A polished company website and business workflow layer built for UniSalesBD using Laravel, jQuery, and responsive UI patterns.",
            "stack": ["Laravel", "jQuery", "PHP"],
            "live_url": "https://unisalesbd.com/",
            "login_url": None,
            "accent": "emerald",
            "cover_image": "./static/assets/images/work02-hover.jpg",
            "role": "Website development",
            "outcome": "A practical business site with a fast content structure and a maintainable backend foundation.",
            "link_label": "Case study",
            "link_url": "/works/unisalesbd",
            "sort_order": 2,
            "is_active": 1,
        },
        {
            "slug": "portfolio-system",
            "number": "03",
            "title": "Portfolio System",
            "summary": "A living personal website with contact, dashboard, SMTP, and expense tools.",
            "description": "The portfolio site you are currently using, including the about page, contact inbox, SMTP controls, and finance tracker.",
            "stack": ["Flask", "SQLite", "GSAP", "Tailwind"],
            "live_url": "./index.html",
            "login_url": None,
            "accent": "rose",
            "cover_image": "./static/assets/images/work03-hover.jpg",
            "role": "Site design and development",
            "outcome": "A content-driven personal website with a private dashboard and dynamic sections.",
            "link_label": "Open site",
            "link_url": "./index.html",
            "sort_order": 3,
            "is_active": 1,
        },
        {
            "slug": "contact-inbox",
            "number": "04",
            "title": "Contact Inbox",
            "summary": "Save incoming messages, mark read or unread, and send auto replies.",
            "description": "Incoming submissions are stored in SQLite and can be reviewed from the dashboard, with automatic replies tied to the stored SMTP config.",
            "stack": ["Flask", "SQLite", "SMTP"],
            "live_url": "./contacts.html",
            "login_url": None,
            "accent": "violet",
            "cover_image": "./static/assets/images/work01-hover.jpg",
            "role": "Inbox workflow",
            "outcome": "A simple message pipeline with read states, replies, and delivery status.",
            "link_label": "View inbox",
            "link_url": "./contacts.html",
            "sort_order": 4,
            "is_active": 1,
        },
        {
            "slug": "expense-tracker",
            "number": "05",
            "title": "Expense Tracker",
            "summary": "Separate money logs for Jim and Nazia, filtered by month.",
            "description": "A monthly personal finance tracker with individual ledgers, charts, and summaries for both users.",
            "stack": ["Flask", "SQLite", "Charts"],
            "live_url": "./dashboard/expenses",
            "login_url": None,
            "accent": "amber",
            "cover_image": "./static/assets/images/work03-hover.jpg",
            "role": "Personal finance tracking",
            "outcome": "A private money log with separate records per account and monthly views.",
            "link_label": "Open tracker",
            "link_url": "./dashboard/expenses",
            "sort_order": 5,
            "is_active": 1,
        },
        {
            "slug": "smtp-manager",
            "number": "06",
            "title": "SMTP Manager",
            "summary": "Store mail server settings and test email delivery from the dashboard.",
            "description": "An internal mail configuration screen for storing SMTP credentials and sending test messages.",
            "stack": ["SMTP", "SQLite", "Flask"],
            "live_url": "./dashboard/smtp-settings",
            "login_url": None,
            "accent": "cyan",
            "cover_image": "./static/assets/images/work02-hover.jpg",
            "role": "Mail configuration",
            "outcome": "A small admin tool for mail delivery testing and configuration management.",
            "link_label": "Open settings",
            "link_url": "./dashboard/smtp-settings",
            "sort_order": 6,
            "is_active": 1,
        },
    ]


def normalize_project_row(project):
    project = dict(project)
    project["title"] = project.get("title", "").strip()
    project["sort_order"] = int(project.get("sort_order") or 0)
    project["number"] = f"{project['sort_order']:02d}" if project["sort_order"] else ""
    project["slug"] = (project.get("slug") or slugify_text(project["title"]))[:120]
    project["summary"] = project.get("summary") or project.get("description", "")
    project["description"] = project.get("description", "")
    project["link_label"] = project.get("link_label") or "Case study"
    project["link_url"] = project.get("link_url") or f"/works/{project['slug']}"
    project["accent"] = project.get("accent") or "sky"
    project["cover_image"] = static_asset_url(project.get("cover_image") or "./static/assets/images/work001-01.jpg")
    project["role"] = project.get("role") or "Project work"
    project["outcome"] = project.get("outcome") or ""
    project["live_url"] = project.get("live_url") or project["link_url"]
    project["login_url"] = project.get("login_url") or None
    stack_json = project.get("stack_json") or "[]"
    try:
        stack = json.loads(stack_json) if isinstance(stack_json, str) else list(stack_json)
    except Exception:
        stack = []
    if not stack:
        if project["slug"] == "ricemill-erp":
            stack = ["TypeScript", "React", "Laravel", "MySQL"]
        elif project["slug"] == "unisalesbd":
            stack = ["Laravel", "jQuery", "PHP"]
        elif project["slug"] == "portfolio-system":
            stack = ["Flask", "SQLite", "GSAP", "Tailwind"]
        elif project["slug"] == "contact-inbox":
            stack = ["Flask", "SQLite", "SMTP"]
        elif project["slug"] == "expense-tracker":
            stack = ["Flask", "SQLite", "Charts"]
        elif project["slug"] == "smtp-manager":
            stack = ["SMTP", "SQLite", "Flask"]
    project["stack"] = stack
    project["stack_json"] = json.dumps(stack)
    return project


def get_portfolio_projects(include_inactive=False):
    visibility_filter = "" if include_inactive else "WHERE is_active = 1"
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT *
            FROM about_projects
            {visibility_filter}
            ORDER BY sort_order ASC, id ASC
            """
        ).fetchall()

    return [normalize_project_row(dict(row)) for row in rows] or get_default_projects()


def get_portfolio_project(slug):
    for project in get_portfolio_projects():
        if project["slug"] == slug:
            return project
    return None


def get_portfolio_project_by_id(project_id):
    if not project_id:
        return None
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM about_projects WHERE id = ?", (project_id,)).fetchone()
    return normalize_project_row(dict(row)) if row else None


def save_about_profile(data):
    fields = {
        "hero_badge": data.get("hero_badge", "").strip(),
        "hero_title": data.get("hero_title", "").strip(),
        "hero_subtitle": data.get("hero_subtitle", "").strip(),
        "intro_label": data.get("intro_label", "").strip(),
        "intro_heading": data.get("intro_heading", "").strip(),
        "intro_text": data.get("intro_text", "").strip(),
        "interests_label": data.get("interests_label", "").strip(),
        "interests_text": data.get("interests_text", "").strip(),
        "focus_label": data.get("focus_label", "").strip(),
        "focus_text": data.get("focus_text", "").strip(),
        "current_label": data.get("current_label", "").strip(),
        "current_text": data.get("current_text", "").strip(),
        "resume_label": data.get("resume_label", "").strip(),
        "resume_url": data.get("resume_url", "").strip(),
        "resume_filename": data.get("resume_filename", "").strip(),
        "portrait_image": data.get("portrait_image", "").strip(),
        "quick_role_label": data.get("quick_role_label", "").strip(),
        "quick_role_value": data.get("quick_role_value", "").strip(),
        "quick_home_label": data.get("quick_home_label", "").strip(),
        "quick_home_value": data.get("quick_home_value", "").strip(),
        "quick_note": data.get("quick_note", "").strip(),
        "timeline_title": data.get("timeline_title", "").strip(),
        "timeline_intro": data.get("timeline_intro", "").strip(),
        "skills_title": data.get("skills_title", "").strip(),
        "skills_intro": data.get("skills_intro", "").strip(),
        "projects_title": data.get("projects_title", "").strip(),
        "projects_intro": data.get("projects_intro", "").strip(),
        "closing_title": data.get("closing_title", "").strip(),
        "closing_text": data.get("closing_text", "").strip(),
    }

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO about_profile (
                id, hero_badge, hero_title, hero_subtitle, intro_label, intro_heading, intro_text,
                interests_label, interests_text, focus_label, focus_text, current_label, current_text,
                resume_label, resume_url, resume_filename, portrait_image,
                quick_role_label, quick_role_value, quick_home_label, quick_home_value, quick_note,
                timeline_title, timeline_intro, skills_title, skills_intro,
                projects_title, projects_intro, closing_title, closing_text
            )
            VALUES (
                1, :hero_badge, :hero_title, :hero_subtitle, :intro_label, :intro_heading, :intro_text,
                :interests_label, :interests_text, :focus_label, :focus_text, :current_label, :current_text,
                :resume_label, :resume_url, :resume_filename, :portrait_image,
                :quick_role_label, :quick_role_value, :quick_home_label, :quick_home_value, :quick_note,
                :timeline_title, :timeline_intro, :skills_title, :skills_intro,
                :projects_title, :projects_intro, :closing_title, :closing_text
            )
            ON CONFLICT(id) DO UPDATE SET
                hero_badge = excluded.hero_badge,
                hero_title = excluded.hero_title,
                hero_subtitle = excluded.hero_subtitle,
                intro_label = excluded.intro_label,
                intro_heading = excluded.intro_heading,
                intro_text = excluded.intro_text,
                interests_label = excluded.interests_label,
                interests_text = excluded.interests_text,
                focus_label = excluded.focus_label,
                focus_text = excluded.focus_text,
                current_label = excluded.current_label,
                current_text = excluded.current_text,
                resume_label = excluded.resume_label,
                resume_url = excluded.resume_url,
                resume_filename = excluded.resume_filename,
                portrait_image = excluded.portrait_image,
                quick_role_label = excluded.quick_role_label,
                quick_role_value = excluded.quick_role_value,
                quick_home_label = excluded.quick_home_label,
                quick_home_value = excluded.quick_home_value,
                quick_note = excluded.quick_note,
                timeline_title = excluded.timeline_title,
                timeline_intro = excluded.timeline_intro,
                skills_title = excluded.skills_title,
                skills_intro = excluded.skills_intro,
                projects_title = excluded.projects_title,
                projects_intro = excluded.projects_intro,
                closing_title = excluded.closing_title,
                closing_text = excluded.closing_text,
                updated_at = CURRENT_TIMESTAMP
            """,
            fields,
        )


def get_timeline_items(include_inactive=False):
    visibility_filter = "" if include_inactive else "WHERE is_active = 1"
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT *
            FROM about_timeline
            {visibility_filter}
            ORDER BY sort_order ASC, id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_timeline_item_by_id(timeline_id):
    if not timeline_id:
        return None
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM about_timeline WHERE id = ?", (timeline_id,)).fetchone()
    return dict(row) if row else None


def save_timeline_item(data):
    title = data.get("title", "").strip()
    if not title:
        raise ValueError("Title is required.")

    timeline_id = data.get("id", "").strip()
    fields = {
        "title": title,
        "description": data.get("description", "").strip(),
        "icon_class": data.get("icon_class", "").strip(),
        "sort_order": int(data.get("sort_order") or 0),
        "is_active": 1 if data.get("is_active") in {"1", "true", "True", "on", "yes"} else 0,
    }

    with sqlite3.connect(DATABASE_PATH) as conn:
        if timeline_id:
            cursor = conn.execute(
                """
                UPDATE about_timeline
                SET title = :title,
                    description = :description,
                    icon_class = :icon_class,
                    sort_order = :sort_order,
                    is_active = :is_active,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {**fields, "id": int(timeline_id)},
            )
            if cursor.rowcount == 0:
                cursor = conn.execute(
                    """
                    INSERT INTO about_timeline (title, description, icon_class, sort_order, is_active)
                    VALUES (:title, :description, :icon_class, :sort_order, :is_active)
                    """,
                    fields,
                )
            return cursor.lastrowid or int(timeline_id)

        cursor = conn.execute(
            """
            INSERT INTO about_timeline (title, description, icon_class, sort_order, is_active)
            VALUES (:title, :description, :icon_class, :sort_order, :is_active)
            """,
            fields,
        )
        return cursor.lastrowid


def save_work_item(data):
    title = data.get("title", "").strip()
    if not title:
        raise ValueError("Title is required.")

    slug = data.get("slug", "").strip() or slugify_text(title)
    stack_raw = data.get("stack", "")
    stack_items = [item.strip() for item in stack_raw.split(",") if item.strip()]
    sort_order = int(data.get("sort_order") or 0)
    is_active = 1 if data.get("is_active") in {"1", "true", "True", "on", "yes"} else 0
    project_id = data.get("id", "").strip()

    fields = {
        "slug": slug,
        "title": title,
        "summary": data.get("summary", "").strip(),
        "description": data.get("description", "").strip(),
        "link_label": data.get("link_label", "").strip() or "Case study",
        "link_url": data.get("link_url", "").strip() or f"/works/{slug}",
        "accent": data.get("accent", "").strip() or "sky",
        "stack_json": json.dumps(stack_items),
        "live_url": data.get("live_url", "").strip(),
        "login_url": data.get("login_url", "").strip(),
        "cover_image": data.get("cover_image", "").strip(),
        "role": data.get("role", "").strip(),
        "outcome": data.get("outcome", "").strip(),
        "sort_order": sort_order,
        "is_active": is_active,
    }

    with sqlite3.connect(DATABASE_PATH) as conn:
        if project_id:
            cursor = conn.execute(
                """
                UPDATE about_projects
                SET slug = :slug,
                    title = :title,
                    summary = :summary,
                    description = :description,
                    link_label = :link_label,
                    link_url = :link_url,
                    accent = :accent,
                    stack_json = :stack_json,
                    live_url = :live_url,
                    login_url = :login_url,
                    cover_image = :cover_image,
                    role = :role,
                    outcome = :outcome,
                    sort_order = :sort_order,
                    is_active = :is_active,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {**fields, "id": int(project_id)},
            )
            if cursor.rowcount == 0:
                conn.execute(
                    """
                    INSERT INTO about_projects (
                        slug, title, summary, description, link_label, link_url, accent, stack_json,
                        live_url, login_url, cover_image, role, outcome, sort_order, is_active
                    )
                    VALUES (
                        :slug, :title, :summary, :description, :link_label, :link_url, :accent, :stack_json,
                        :live_url, :login_url, :cover_image, :role, :outcome, :sort_order, :is_active
                    )
                    """,
                    fields,
                )
        else:
            conn.execute(
                """
                INSERT INTO about_projects (
                    slug, title, summary, description, link_label, link_url, accent, stack_json,
                    live_url, login_url, cover_image, role, outcome, sort_order, is_active
                )
                VALUES (
                    :slug, :title, :summary, :description, :link_label, :link_url, :accent, :stack_json,
                    :live_url, :login_url, :cover_image, :role, :outcome, :sort_order, :is_active
                )
                """,
                fields,
            )

@app.after_request
def add_last_modified_header(resp):
    dt = _last_commit_datetime()
    if dt:
        resp.headers['Last-Modified'] = http_date(dt.timestamp())
    return resp


def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entry_type TEXT NOT NULL CHECK (entry_type IN ('expense', 'income')),
                purpose TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                owner_notification_sent INTEGER NOT NULL DEFAULT 0,
                auto_reply_sent INTEGER NOT NULL DEFAULT 0,
                owner_notification_error TEXT NOT NULL DEFAULT '',
                auto_reply_error TEXT NOT NULL DEFAULT '',
                read_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        existing_contact_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(contacts)").fetchall()
        }
        if "staff_reply_sent" not in existing_contact_cols:
            conn.execute("ALTER TABLE contacts ADD COLUMN staff_reply_sent INTEGER NOT NULL DEFAULT 0")
        if "staff_reply_error" not in existing_contact_cols:
            conn.execute("ALTER TABLE contacts ADD COLUMN staff_reply_error TEXT NOT NULL DEFAULT ''")
        if "staff_reply_at" not in existing_contact_cols:
            conn.execute("ALTER TABLE contacts ADD COLUMN staff_reply_at TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS smtp_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                host TEXT NOT NULL DEFAULT '',
                port INTEGER NOT NULL DEFAULT 465,
                encryption TEXT NOT NULL DEFAULT 'SSL',
                username TEXT NOT NULL DEFAULT '',
                password TEXT NOT NULL DEFAULT '',
                from_name TEXT NOT NULL DEFAULT '',
                from_address TEXT NOT NULL DEFAULT '',
                timeout_sec INTEGER NOT NULL DEFAULT 60,
                is_active INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO smtp_settings (
                id, host, port, encryption, username, password,
                from_name, from_address, timeout_sec, is_active
            )
            VALUES (1, '', 465, 'SSL', '', '', '', '', 60, 1)
            """
        )

        conn.execute(
            "DELETE FROM users WHERE username IN (?, ?)",
            ("me", "wife"),
        )
        conn.execute(
            """
            INSERT INTO users (username, display_name, password_hash, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(username) DO NOTHING
            """,
            (
                "tanjilurrahman21@gmail.com",
                "Jim",
                generate_password_hash("123456"),
            ),
        )
        conn.execute(
            """
            INSERT INTO users (username, display_name, password_hash, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(username) DO NOTHING
            """,
            (
                "nazianuzhat90@gmail.com",
                "Nazia",
                generate_password_hash("123456"),
            ),
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS about_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                hero_badge TEXT NOT NULL DEFAULT '03 : About me',
                hero_title TEXT NOT NULL DEFAULT 'A little about Jim',
                hero_subtitle TEXT NOT NULL DEFAULT '',
                intro_label TEXT NOT NULL DEFAULT 'Who I am',
                intro_heading TEXT NOT NULL DEFAULT 'Hello,',
                intro_text TEXT NOT NULL DEFAULT '',
                interests_label TEXT NOT NULL DEFAULT 'Interests & hobbies',
                interests_text TEXT NOT NULL DEFAULT '',
                focus_label TEXT NOT NULL DEFAULT 'Focus',
                focus_text TEXT NOT NULL DEFAULT '',
                current_label TEXT NOT NULL DEFAULT 'Currently into',
                current_text TEXT NOT NULL DEFAULT '',
                resume_label TEXT NOT NULL DEFAULT 'Download My Resume',
                resume_url TEXT NOT NULL DEFAULT '',
                resume_filename TEXT NOT NULL DEFAULT '',
                portrait_image TEXT NOT NULL DEFAULT '',
                quick_role_label TEXT NOT NULL DEFAULT 'Role',
                quick_role_value TEXT NOT NULL DEFAULT '',
                quick_home_label TEXT NOT NULL DEFAULT 'Home base',
                quick_home_value TEXT NOT NULL DEFAULT '',
                quick_note TEXT NOT NULL DEFAULT '',
                timeline_title TEXT NOT NULL DEFAULT 'Timeline',
                timeline_intro TEXT NOT NULL DEFAULT '',
                skills_title TEXT NOT NULL DEFAULT 'Skills',
                skills_intro TEXT NOT NULL DEFAULT '',
                projects_title TEXT NOT NULL DEFAULT 'Projects',
                projects_intro TEXT NOT NULL DEFAULT '',
                closing_title TEXT NOT NULL DEFAULT 'Could add next',
                closing_text TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS about_social_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                icon_class TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS about_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                icon_class TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS about_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                accent TEXT NOT NULL DEFAULT 'sky',
                icon_class TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS about_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                link_label TEXT NOT NULL DEFAULT 'Open',
                link_url TEXT NOT NULL DEFAULT '',
                accent TEXT NOT NULL DEFAULT 'sky',
                stack_json TEXT NOT NULL DEFAULT '[]',
                live_url TEXT NOT NULL DEFAULT '',
                login_url TEXT NOT NULL DEFAULT '',
                cover_image TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT '',
                outcome TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        skill_columns = {row[1] for row in conn.execute("PRAGMA table_info(about_skills)").fetchall()}
        if "icon_class" not in skill_columns:
            conn.execute("ALTER TABLE about_skills ADD COLUMN icon_class TEXT NOT NULL DEFAULT ''")

        project_columns = {row[1] for row in conn.execute("PRAGMA table_info(about_projects)").fetchall()}
        project_column_defaults = {
            "slug": "ALTER TABLE about_projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''",
            "summary": "ALTER TABLE about_projects ADD COLUMN summary TEXT NOT NULL DEFAULT ''",
            "stack_json": "ALTER TABLE about_projects ADD COLUMN stack_json TEXT NOT NULL DEFAULT '[]'",
            "live_url": "ALTER TABLE about_projects ADD COLUMN live_url TEXT NOT NULL DEFAULT ''",
            "login_url": "ALTER TABLE about_projects ADD COLUMN login_url TEXT NOT NULL DEFAULT ''",
            "cover_image": "ALTER TABLE about_projects ADD COLUMN cover_image TEXT NOT NULL DEFAULT ''",
            "role": "ALTER TABLE about_projects ADD COLUMN role TEXT NOT NULL DEFAULT ''",
            "outcome": "ALTER TABLE about_projects ADD COLUMN outcome TEXT NOT NULL DEFAULT ''",
        }
        for column_name, alter_sql in project_column_defaults.items():
            if column_name not in project_columns:
                conn.execute(alter_sql)

        if conn.execute("SELECT COUNT(*) FROM about_profile").fetchone()[0] == 0:
            conn.execute(
                """
                INSERT INTO about_profile (
                    id, hero_badge, hero_title, hero_subtitle, intro_label, intro_heading, intro_text,
                    interests_label, interests_text, focus_label, focus_text, current_label, current_text,
                    resume_label, resume_url, resume_filename, portrait_image,
                    quick_role_label, quick_role_value, quick_home_label, quick_home_value, quick_note,
                    timeline_title, timeline_intro, skills_title, skills_intro,
                    projects_title, projects_intro, closing_title, closing_text
                )
                VALUES (
                    1, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    "03 : About me",
                    "A little about Jim",
                    "A clean story page with a bit of motion, a bit of personality, and enough structure to show who you are without feeling crowded.",
                    "Who I am",
                    "Hello,",
                    "I'm Tanjilur but you can call me Jim. I am a graduate of CSE dept from Brac University, I am an aspiring fullstack developer and I have explored machine learning through my thesis on multi-modal analysis of EEG and fMRI for sleep stage classification using deep learning.",
                    "Interests & hobbies",
                    "Outside academics, I love to travel. I'm passionate about music, playing bass, rapping, and writing poetry. A die-hard Liverpool fan, I also enjoy chess, watching football, and e-sports like Valorant, FIFA, RDR 2, Spiderman, and Fortnite. Check out my YouTube channel for more.",
                    "Focus",
                    "Full-stack development, clean UI, useful systems, and interactive experiences.",
                    "Currently into",
                    "Personal portfolio work, Flask apps, and motion-led storytelling on the web.",
                    "Download My Resume",
                    "./static/assets/Resume_of_Tanjilur_Rahman.pdf",
                    "Resume_of_Tanjilur_Rahman.pdf",
                    "./static/assets/images/2.jpg",
                    "Role",
                    "Full-stack enthusiast",
                    "Home base",
                    "Portfolio builder",
                    "Scroll a little and the floating layers and image will drift subtly to create a soft parallax feel.",
                    "Timeline",
                    "A few key beats from the path so far.",
                    "Skills",
                    "A small horizontal strip of the tools and strengths that show up most often.",
                    "Projects",
                    "Cards that can later be edited from the dashboard as the site grows.",
                    "Could add next",
                    "A skills strip, a featured projects band, a testimonial quote, or a \"now\" section. Those make About pages feel richer than a plain biography.",
                ),
            )

        if conn.execute("SELECT COUNT(*) FROM about_social_links").fetchone()[0] == 0:
            conn.executemany(
                """
                INSERT INTO about_social_links (label, icon_class, url, sort_order, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                [
                    ("GitHub", "fab fa-github", "https://github.com/TanjilurJim", 1),
                    ("LinkedIn", "fab fa-linkedin-in", "http://www.linkedin.com/in/tanjilur-rahman-jim", 2),
                    ("Facebook", "fab fa-facebook-f", "https://www.facebook.com/RageAgainstJim/", 3),
                    ("Instagram", "fab fa-instagram", "https://www.instagram.com/rage.against.jim", 4),
                    ("Twitter", "fab fa-twitter", "https://twitter.com/4thSpiderman", 5),
                ],
            )

        if conn.execute("SELECT COUNT(*) FROM about_timeline").fetchone()[0] == 0:
            conn.executemany(
                """
                INSERT INTO about_timeline (title, description, icon_class, sort_order, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                [
                    ("Brac University / CSE", "Learned the structure behind software, built projects, and explored thesis work in EEG and fMRI analysis.", "fas fa-university", 1),
                    ("Research focus", "Worked with multi-modal analysis and deep learning to understand sleep stage classification better.", "fas fa-flask", 2),
                    ("Building in public", "Shaping a personal portfolio with Flask, SQLite, and practical dashboard tools instead of just a static resume.", "fas fa-pen-nib", 3),
                    ("Next direction", "More polished interfaces, more automation, and more pages that feel alive when you scroll through them.", "fas fa-arrow-right", 4),
                ],
            )

        skill_titles = {row[0] for row in conn.execute("SELECT title FROM about_skills").fetchall()}
        legacy_skill_titles = {"Flask", "SQLite", "GSAP", "Tailwind", "Machine Learning"}
        if not skill_titles or skill_titles.issubset(legacy_skill_titles):
            conn.execute("DELETE FROM about_skills")
            conn.executemany(
                """
                INSERT INTO about_skills (title, description, accent, icon_class, sort_order, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                [
                    ("Python", "Flask apps, data handling, scripting, and backend logic.", "sky", "fab fa-python", 1),
                    ("Django", "Structured Python web development and admin-style patterns.", "emerald", "fas fa-server", 2),
                    ("PHP", "Legacy and practical server-side work across client projects.", "amber", "fab fa-php", 3),
                    ("CodeIgniter", "Lightweight PHP framework work for fast delivery.", "violet", "fas fa-bolt", 4),
                    ("Laravel", "Robust backend APIs, Inertia stacks, and business tooling.", "rose", "fab fa-laravel", 5),
                    ("JavaScript", "Frontend behavior, interfaces, and interactive UI logic.", "sky", "fab fa-js-square", 6),
                    ("React", "Component-driven UI for modern app frontends.", "cyan", "fab fa-react", 7),
                    ("Next.js", "Next-level React apps and app-router style web experiences.", "slate", "fas fa-layer-group", 8),
                    ("TypeScript", "Safer frontend and backend code with typed structures.", "indigo", "fas fa-code", 9),
                    ("AWS", "Deployment, hosting, and cloud-ready architecture.", "orange", "fab fa-aws", 10),
                    ("GSAP", "Motion-led storytelling, parallax, and cinematic entrances.", "pink", "fas fa-wand-magic-sparkles", 11),
                    ("Tailwind", "Fast visual polish with responsive layouts and strong hierarchy.", "violet", "fas fa-wind", 12),
                    ("Machine Learning", "Research exposure through EEG and fMRI sleep stage classification.", "amber", "fas fa-brain", 13),
                ],
            )

        project_titles = {row[0] for row in conn.execute("SELECT title FROM about_projects").fetchall()}
        legacy_project_titles = {"Portfolio System", "Contact Inbox", "Expense Tracker", "SMTP Manager"}
        if not project_titles or project_titles.issubset(legacy_project_titles):
            conn.execute("DELETE FROM about_projects")
            conn.executemany(
                """
                INSERT INTO about_projects (
                    slug, title, summary, description, link_label, link_url, accent, stack_json,
                    live_url, login_url, cover_image, role, outcome, sort_order, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                [
                    (
                        "ricemill-erp",
                        "RiceMill ERP",
                        "ERP software for rice mill operations with TypeScript, React, Laravel, and MySQL.",
                        "A business system built to manage rice mill workflows, operations, and records with a modern TypeScript and React frontend backed by Laravel and MySQL.",
                        "Case study",
                        "/works/ricemill-erp",
                        "sky",
                        json.dumps(["TypeScript", "React", "Laravel", "MySQL"]),
                        "https://ricemillerp.com/",
                        "https://ricemillerp.com/login",
                        "./static/assets/images/work001-01.jpg",
                        "Full-stack development",
                        "A tailored ERP experience with clean flows, structured data handling, and business-focused screens.",
                        1,
                    ),
                    (
                        "unisalesbd",
                        "UniSalesBD",
                        "Laravel and jQuery-based business site for sales operations and presentation.",
                        "A polished company website and business workflow layer built for UniSalesBD using Laravel, jQuery, and responsive UI patterns.",
                        "Case study",
                        "/works/unisalesbd",
                        "emerald",
                        json.dumps(["Laravel", "jQuery", "PHP"]),
                        "https://unisalesbd.com/",
                        "",
                        "./static/assets/images/work02-hover.jpg",
                        "Website development",
                        "A practical business site with a fast content structure and a maintainable backend foundation.",
                        2,
                    ),
                    (
                        "portfolio-system",
                        "Portfolio System",
                        "A living personal website with contact, dashboard, SMTP, and expense tools.",
                        "The portfolio site you are currently using, including the about page, contact inbox, SMTP controls, and finance tracker.",
                        "Open site",
                        "./index.html",
                        "rose",
                        json.dumps(["Flask", "SQLite", "GSAP", "Tailwind"]),
                        "./index.html",
                        "",
                        "./static/assets/images/work03-hover.jpg",
                        "Site design and development",
                        "A content-driven personal website with a private dashboard and dynamic sections.",
                        3,
                    ),
                    (
                        "contact-inbox",
                        "Contact Inbox",
                        "Save incoming messages, mark read or unread, and send auto replies.",
                        "Incoming submissions are stored in SQLite and can be reviewed from the dashboard, with automatic replies tied to the stored SMTP config.",
                        "View inbox",
                        "./contacts.html",
                        "violet",
                        json.dumps(["Flask", "SQLite", "SMTP"]),
                        "./contacts.html",
                        "",
                        "./static/assets/images/work01-hover.jpg",
                        "Inbox workflow",
                        "A simple message pipeline with read states, replies, and delivery status.",
                        4,
                    ),
                    (
                        "expense-tracker",
                        "Expense Tracker",
                        "Separate money logs for Jim and Nazia, filtered by month.",
                        "A monthly personal finance tracker with individual ledgers, charts, and summaries for both users.",
                        "Open tracker",
                        "./dashboard/expenses",
                        "amber",
                        json.dumps(["Flask", "SQLite", "Charts"]),
                        "./dashboard/expenses",
                        "",
                        "./static/assets/images/work03-hover.jpg",
                        "Personal finance tracking",
                        "A private money log with separate records per account and monthly views.",
                        5,
                    ),
                    (
                        "smtp-manager",
                        "SMTP Manager",
                        "Store mail server settings and test email delivery from the dashboard.",
                        "An internal mail configuration screen for storing SMTP credentials and sending test messages.",
                        "Open settings",
                        "./dashboard/smtp-settings",
                        "cyan",
                        json.dumps(["SMTP", "SQLite", "Flask"]),
                        "./dashboard/smtp-settings",
                        "",
                        "./static/assets/images/work02-hover.jpg",
                        "Mail configuration",
                        "A small admin tool for mail delivery testing and configuration management.",
                        6,
                    ),
                ],
            )


if os.environ.get("PORTFOLIO_SKIP_AUTO_DB_INIT") != "1":
    init_db()


def get_current_user():
    username = session.get("username")
    if not username:
        return None

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, username, display_name
            FROM users
            WHERE username = ? AND is_active = 1
            """,
            (username,),
        ).fetchone()
        return dict(row) if row else None


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


@app.route('/')
def my_home():
    return render_template('index.html')

@app.route('/<string:page_name>')
def html_page(page_name):
    if page_name == 'dashboard.html':
        return redirect(url_for('dashboard'))
    if page_name == 'login.html':
        return redirect(url_for('login'))
    if page_name == 'about.html':
        return render_template('about.html', about_data=get_about_page_data())
    if page_name == 'works.html':
        work_items = get_portfolio_projects()
        return render_template('works.html', work_items=work_items, work_groups=[work_items[i:i + 3] for i in range(0, len(work_items), 3)])
    if page_name == 'work.html':
        return redirect(url_for('project_detail', slug='ricemill-erp'))
    if page_name == 'smtp_settings.html':
        return redirect(url_for('smtp_settings'))
    if page_name == 'expenses.html':
        return redirect(url_for('expenses'))
    if page_name == 'contacts.html':
        return redirect(url_for('contacts'))
    if page_name == 'contact_detail.html':
        return redirect(url_for('contacts'))
    return render_template(page_name)


@app.route('/works')
def works():
    work_items = get_portfolio_projects()
    return render_template('works.html', work_items=work_items, work_groups=[work_items[i:i + 3] for i in range(0, len(work_items), 3)])


@app.route('/works/<slug>')
def project_detail(slug):
    project = get_portfolio_project(slug)
    if not project:
        return redirect(url_for('works'))
    return render_template('project_detail.html', project=project, work_items=get_portfolio_projects())


def save_contact_submission(data):
    email = data["email"].strip()
    subject = data["subject"].strip()
    message = data["message"].strip()

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO contacts (email, subject, message)
            VALUES (?, ?, ?)
            """,
            (email, subject, message),
        )
        return cursor.lastrowid


def get_smtp_settings():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT host, port, encryption, username, password,
                   from_name, from_address, timeout_sec, is_active, updated_at
            FROM smtp_settings
            WHERE id = 1
            """
        ).fetchone()
        return dict(row) if row else None


def get_current_user_id():
    user = get_current_user()
    return user["id"] if user else None


def normalize_month_key(month_key):
    fallback = datetime.now().strftime("%Y-%m")
    if not month_key:
        return fallback
    try:
        datetime.strptime(month_key, "%Y-%m")
        return month_key
    except ValueError:
        return fallback


def get_expense_users():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, username, display_name
            FROM users
            WHERE is_active = 1
            ORDER BY display_name COLLATE NOCASE
            """
        ).fetchall()
        return [dict(row) for row in rows]


def save_transaction(user_id, data):
    entry_type = data.get("entry_type", "expense").strip().lower()
    if entry_type not in {"expense", "income"}:
        raise ValueError("Invalid entry type.")

    purpose = data.get("purpose", "").strip()
    if not purpose:
        raise ValueError("Purpose is required.")

    amount_raw = data.get("amount", "").strip()
    if not amount_raw:
        raise ValueError("Amount is required.")

    amount = float(amount_raw)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    transaction_date = data.get("transaction_date", "").strip() or date.today().isoformat()
    note = data.get("note", "").strip()

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO transactions (
                user_id, entry_type, purpose, amount, transaction_date, note, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, entry_type, purpose, amount, transaction_date, note),
        )


def get_available_expense_months(selected_month):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT DISTINCT strftime('%Y-%m', transaction_date) AS month_key
            FROM transactions
            WHERE transaction_date IS NOT NULL AND transaction_date != ''
            ORDER BY month_key DESC
            """
        ).fetchall()

    months = [row["month_key"] for row in rows if row["month_key"]]
    if selected_month not in months:
        months.insert(0, selected_month)
    if not months:
        months = [selected_month]

    options = []
    for month in months:
        try:
            label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
        except ValueError:
            label = month
        options.append({"value": month, "label": label})
    return options


def get_expense_overview(month_key=None):
    month_key = normalize_month_key(month_key)
    month_label = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
    current_user = get_current_user()
    current_user_id = current_user["id"] if current_user else None
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        user_rows = conn.execute(
            """
            SELECT
                u.id AS user_id,
                u.username,
                u.display_name
            FROM users u
            WHERE u.is_active = 1
            ORDER BY u.display_name COLLATE NOCASE
            """,
        ).fetchall()

        summary_rows = conn.execute(
            """
            SELECT
                u.id AS user_id,
                COALESCE(SUM(CASE WHEN t.entry_type = 'income' THEN t.amount ELSE 0 END), 0) AS income_total,
                COALESCE(SUM(CASE WHEN t.entry_type = 'expense' THEN t.amount ELSE 0 END), 0) AS expense_total
            FROM users u
            LEFT JOIN transactions t
                ON t.user_id = u.id
               AND strftime('%Y-%m', t.transaction_date) = ?
            WHERE u.is_active = 1
            GROUP BY u.id
            ORDER BY u.id
            """,
            (month_key,),
        ).fetchall()

        purpose_rows = conn.execute(
            """
            SELECT
                purpose,
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE entry_type = 'expense'
              AND strftime('%Y-%m', transaction_date) = ?
              AND user_id = ?
            GROUP BY purpose
            ORDER BY total DESC, purpose COLLATE NOCASE
            """,
            (month_key, current_user_id),
        ).fetchall()

        history_rows = conn.execute(
            """
            SELECT
                t.id,
                t.user_id,
                u.display_name,
                t.entry_type,
                t.purpose,
                t.amount,
                t.transaction_date,
                t.note,
                t.created_at
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            WHERE strftime('%Y-%m', t.transaction_date) = ?
              AND t.user_id = ?
            ORDER BY date(t.transaction_date) DESC, t.id DESC
            """
            ,
            (month_key, current_user_id),
        ).fetchall()

    purpose_breakdown = []
    purpose_total = sum(float(row["total"]) for row in purpose_rows) if purpose_rows else 0.0
    for row in purpose_rows:
        amount_value = float(row["total"] or 0)
        percent = round((amount_value / purpose_total) * 100, 1) if purpose_total else 0
        purpose_breakdown.append(
            {
                "purpose": row["purpose"],
                "amount": amount_value,
                "percent": percent,
            }
        )

    summary_lookup = {
        row["user_id"]: row for row in summary_rows
    }

    user_summaries = []
    for row in user_rows:
        summary = summary_lookup.get(row["user_id"], {})
        income_total = float(summary["income_total"] or 0) if summary else 0.0
        expense_total = float(summary["expense_total"] or 0) if summary else 0.0
        user_summaries.append(
            {
                "user_id": row["user_id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "income_total": income_total,
                "expense_total": expense_total,
                "net_total": income_total - expense_total,
            }
        )

    current_user_summary = next(
        (row for row in user_summaries if row["user_id"] == current_user_id),
        None,
    )
    other_user_summary = next(
        (row for row in user_summaries if row["user_id"] != current_user_id),
        None,
    )

    current_user_income = float(current_user_summary["income_total"] or 0) if current_user_summary else 0.0
    current_user_expense = float(current_user_summary["expense_total"] or 0) if current_user_summary else 0.0
    other_user_income = float(other_user_summary["income_total"] or 0) if other_user_summary else 0.0
    other_user_expense = float(other_user_summary["expense_total"] or 0) if other_user_summary else 0.0

    return {
        "month_key": month_key,
        "month_label": month_label,
        "current_user_income": current_user_income,
        "current_user_expense": current_user_expense,
        "current_user_balance": current_user_income - current_user_expense,
        "other_user_income": other_user_income,
        "other_user_expense": other_user_expense,
        "other_user_balance": other_user_income - other_user_expense,
        "user_summaries": user_summaries,
        "current_user_summary": current_user_summary,
        "other_user_summary": other_user_summary,
        "purpose_breakdown": purpose_breakdown,
        "purpose_labels": [row["purpose"] for row in purpose_breakdown],
        "purpose_values": [row["amount"] for row in purpose_breakdown],
        "history_rows": [dict(row) for row in history_rows],
    }


def get_contacts():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, email, subject, message, is_read,
                   owner_notification_sent, auto_reply_sent,
                   owner_notification_error, auto_reply_error,
                   staff_reply_sent, staff_reply_error, staff_reply_at,
                   read_at, created_at, updated_at
            FROM contacts
            ORDER BY datetime(created_at) DESC, id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_contact(contact_id):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, email, subject, message, is_read,
                   owner_notification_sent, auto_reply_sent,
                   owner_notification_error, auto_reply_error,
                   staff_reply_sent, staff_reply_error, staff_reply_at,
                   read_at, created_at, updated_at
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        ).fetchone()
        return dict(row) if row else None


def mark_contact_read(contact_id):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE contacts
            SET is_read = 1,
                read_at = COALESCE(read_at, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (contact_id,),
        )


def update_contact_delivery_status(contact_id, *, owner_sent=None, auto_sent=None, owner_error=None, auto_error=None, staff_sent=None, staff_error=None, staff_at=None):
    fields = []
    values = []

    if owner_sent is not None:
        fields.append("owner_notification_sent = ?")
        values.append(1 if owner_sent else 0)
    if auto_sent is not None:
        fields.append("auto_reply_sent = ?")
        values.append(1 if auto_sent else 0)
    if owner_error is not None:
        fields.append("owner_notification_error = ?")
        values.append(owner_error)
    if auto_error is not None:
        fields.append("auto_reply_error = ?")
        values.append(auto_error)
    if staff_sent is not None:
        fields.append("staff_reply_sent = ?")
        values.append(1 if staff_sent else 0)
    if staff_error is not None:
        fields.append("staff_reply_error = ?")
        values.append(staff_error)
    if staff_at is not None:
        fields.append("staff_reply_at = ?")
        values.append(staff_at)

    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(contact_id)

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            f"""
            UPDATE contacts
            SET {", ".join(fields)}
            WHERE id = ?
            """,
            values,
        )


def save_smtp_settings(data):
    host = data.get("host", "").strip()
    port = int(data.get("port", 465))
    encryption = data.get("encryption", "SSL").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    from_name = data.get("from_name", "").strip()
    from_address = data.get("from_address", "").strip()
    timeout_sec = int(data.get("timeout_sec", 60))
    is_active = 1 if str(data.get("is_active", "1")).lower() in {"1", "true", "on", "yes"} else 0

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO smtp_settings (
                id, host, port, encryption, username, password,
                from_name, from_address, timeout_sec, is_active, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                host = excluded.host,
                port = excluded.port,
                encryption = excluded.encryption,
                username = excluded.username,
                password = excluded.password,
                from_name = excluded.from_name,
                from_address = excluded.from_address,
                timeout_sec = excluded.timeout_sec,
                is_active = excluded.is_active,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                1,
                host,
                port,
                encryption,
                username,
                password,
                from_name,
                from_address,
                timeout_sec,
                is_active,
            ),
        )


def build_contact_email_text(contact, site_name="Tanjilur Rahman"):
    return (
        f"New contact message from {contact['email']}\n\n"
        f"Subject: {contact['subject']}\n"
        f"Message:\n{contact['message']}\n"
    )


def build_contact_email_html(contact, site_name="Tanjilur Rahman"):
    sender_email = html.escape(contact["email"])
    subject = html.escape(contact["subject"])
    message = html.escape(contact["message"]).replace("\n", "<br>")

    return f"""
    <div style="margin:0;padding:0;background:#f3f4f6;font-family:Roboto Mono,Menlo,monospace;">
      <div style="max-width:680px;margin:0 auto;padding:32px 16px;">
        <div style="background:#0b0b0b;color:#f8f8f8;border:1px solid #2b2b2b;border-radius:24px;overflow:hidden;">
          <div style="padding:28px 30px;border-bottom:1px solid #2b2b2b;">
            <div style="font-size:12px;letter-spacing:.35em;text-transform:uppercase;color:#a3a3a3;">New Contact</div>
            <h1 style="margin:14px 0 0;font-size:28px;line-height:1.2;">You received a new message</h1>
            <p style="margin:12px 0 0;color:#cfcfcf;line-height:1.7;">A visitor sent a message through your portfolio contact form.</p>
          </div>
          <div style="padding:28px 30px;">
            <div style="display:block;margin-bottom:18px;">
              <div style="font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#9ca3af;margin-bottom:8px;">From</div>
              <div style="font-size:16px;color:#ffffff;">{sender_email}</div>
            </div>
            <div style="display:block;margin-bottom:18px;">
              <div style="font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#9ca3af;margin-bottom:8px;">Subject</div>
              <div style="font-size:16px;color:#ffffff;">{subject}</div>
            </div>
            <div style="display:block;">
              <div style="font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#9ca3af;margin-bottom:8px;">Message</div>
              <div style="font-size:15px;line-height:1.8;color:#e5e7eb;background:#111111;border:1px solid #2b2b2b;border-radius:18px;padding:18px 20px;">{message}</div>
            </div>
          </div>
          <div style="padding:0 30px 28px;color:#9ca3af;font-size:12px;line-height:1.7;">
            <p>This message was sent from {site_name}'s contact page.</p>
          </div>
        </div>
      </div>
    </div>
    """


def build_auto_reply_text(contact, site_name="Tanjilur Rahman"):
    return (
        f"Hi {contact['email']},\n\n"
        f"Thanks for reaching out through the portfolio site.\n"
        f"I have received your message about:\n"
        f"{contact['subject']}\n\n"
        f"I will get back to you as soon as possible.\n\n"
        f"Best,\n{site_name}\n"
    )


def build_auto_reply_html(contact, site_name="Tanjilur Rahman"):
    subject = html.escape(contact["subject"])
    return f"""
    <div style="margin:0;padding:0;background:#f3f4f6;font-family:Roboto Mono,Menlo,monospace;">
      <div style="max-width:680px;margin:0 auto;padding:32px 16px;">
        <div style="background:#ffffff;color:#111111;border:1px solid #d1d5db;border-radius:24px;overflow:hidden;box-shadow:0 12px 30px rgba(0,0,0,.08);">
          <div style="padding:28px 30px;border-bottom:1px solid #e5e7eb;background:linear-gradient(135deg,#111111,#2b2b2b);color:#ffffff;">
            <div style="font-size:12px;letter-spacing:.35em;text-transform:uppercase;color:#d1d5db;">Thanks for writing</div>
            <h1 style="margin:14px 0 0;font-size:28px;line-height:1.2;">Message received</h1>
            <p style="margin:12px 0 0;color:#e5e7eb;line-height:1.7;">Your message about <strong>{subject}</strong> has been received.</p>
          </div>
          <div style="padding:28px 30px;">
            <p style="margin:0 0 16px;line-height:1.8;color:#111111;">Hi there,</p>
            <p style="margin:0 0 16px;line-height:1.8;color:#111111;">Thanks for reaching out through my portfolio site. I’ve received your message and I’ll get back to you as soon as I can.</p>
            <p style="margin:0;line-height:1.8;color:#111111;">Best regards,<br>{html.escape(site_name)}</p>
          </div>
          <div style="padding:0 30px 28px;color:#6b7280;font-size:12px;line-height:1.7;">
            <p>This is an automated response from the portfolio contact form.</p>
          </div>
        </div>
      </div>
    </div>
    """


def build_staff_reply_text(contact, subject, body, site_name="Tanjilur Rahman"):
    return (
        f"Hi {contact['email']},\n\n"
        f"{body}\n\n"
        f"Best,\n{site_name}\n"
    )


def build_staff_reply_html(contact, subject, body, site_name="Tanjilur Rahman"):
    safe_subject = html.escape(subject)
    safe_body = html.escape(body).replace("\n", "<br>")
    return f"""
    <div style="margin:0;padding:0;background:#f3f4f6;font-family:Roboto Mono,Menlo,monospace;">
      <div style="max-width:680px;margin:0 auto;padding:32px 16px;">
        <div style="background:#0b0b0b;color:#f8f8f8;border:1px solid #2b2b2b;border-radius:24px;overflow:hidden;">
          <div style="padding:28px 30px;border-bottom:1px solid #2b2b2b;">
            <div style="font-size:12px;letter-spacing:.35em;text-transform:uppercase;color:#a3a3a3;">Reply</div>
            <h1 style="margin:14px 0 0;font-size:28px;line-height:1.2;">{safe_subject}</h1>
            <p style="margin:12px 0 0;color:#cfcfcf;line-height:1.7;">Replying to {html.escape(contact["email"])}</p>
          </div>
          <div style="padding:28px 30px;">
            <div style="font-size:15px;line-height:1.8;color:#e5e7eb;background:#111111;border:1px solid #2b2b2b;border-radius:18px;padding:18px 20px;">{safe_body}</div>
          </div>
          <div style="padding:0 30px 28px;color:#9ca3af;font-size:12px;line-height:1.7;">
            <p>This reply was sent from {html.escape(site_name)}.</p>
          </div>
        </div>
      </div>
    </div>
    """


def send_reply_to_contact(contact, reply_subject, reply_body):
    smtp_settings_row = get_smtp_settings()
    if not smtp_settings_row or int(smtp_settings_row.get("is_active", 1)) != 1:
        raise ValueError("SMTP settings are inactive or missing.")

    send_smtp_email(
        smtp_settings_row,
        contact["email"],
        reply_subject,
        build_staff_reply_text(contact, reply_subject, reply_body),
        build_staff_reply_html(contact, reply_subject, reply_body),
        reply_to=smtp_settings_row.get("from_address") or smtp_settings_row.get("username") or OWNER_NOTIFY_EMAIL,
    )


def send_smtp_email(smtp_data, recipient, subject, text_body, html_body=None, reply_to=None):
    host = smtp_data.get("host", "").strip()
    port = int(smtp_data.get("port", 465))
    encryption = smtp_data.get("encryption", "SSL").strip().upper()
    username = smtp_data.get("username", "").strip()
    password = smtp_data.get("password", "").strip()
    from_name = smtp_data.get("from_name", "").strip() or "Portfolio App"
    from_address = smtp_data.get("from_address", "").strip() or username
    timeout_sec = int(smtp_data.get("timeout_sec", 60))

    if not host:
        raise ValueError("SMTP host is required.")
    if not from_address:
        raise ValueError("From address is required.")
    if not recipient:
        raise ValueError("Recipient is required.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_address}>"
    message["To"] = recipient
    if reply_to:
        message["Reply-To"] = reply_to

    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()

    if encryption == "SSL":
        with smtplib.SMTP_SSL(host, port, timeout=timeout_sec, context=context) as server:
            if username:
                server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host, port, timeout=timeout_sec) as server:
        server.ehlo()
        if encryption == "TLS":
            server.starttls(context=context)
            server.ehlo()
        if username:
            server.login(username, password)
        server.send_message(message)


def send_test_email(smtp_data, recipient):
    send_smtp_email(
        smtp_data,
        recipient,
        "Portfolio SMTP Test",
        (
            "This is a test email from your portfolio app.\n\n"
            f"Host: {smtp_data.get('host', '').strip()}\n"
            f"Port: {smtp_data.get('port', 465)}\n"
            f"Encryption: {smtp_data.get('encryption', 'SSL').strip().upper()}\n"
        ),
    )


def authenticate_user(username, password):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, username, display_name, password_hash
            FROM users
            WHERE username = ? AND is_active = 1
            """,
            (username,),
        ).fetchone()

    if not row:
        return None

    if not check_password_hash(row["password_hash"], password):
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
    }


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('login.html', current_user=get_current_user())


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        totals = conn.execute(
            """
            SELECT
                COALESCE(COUNT(*), 0) AS total_contacts,
                COALESCE(SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END), 0) AS unread_contacts,
                COALESCE(SUM(CASE WHEN owner_notification_sent = 1 THEN 1 ELSE 0 END), 0) AS owner_notifications_sent,
                COALESCE(SUM(CASE WHEN auto_reply_sent = 1 THEN 1 ELSE 0 END), 0) AS auto_replies_sent
            FROM contacts
            """
        ).fetchone()
        timeline_totals = conn.execute(
            """
            SELECT
                COALESCE(COUNT(*), 0) AS total_timeline_items,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active_timeline_items
            FROM about_timeline
            """
        ).fetchone()

    expense_data = get_expense_overview()
    return render_template(
        'dashboard.html',
        current_user=get_current_user(),
        contact_totals=dict(totals) if totals else {},
        timeline_totals=dict(timeline_totals) if timeline_totals else {},
        expense_data=expense_data,
    )


@app.route('/dashboard/about-profile', methods=['POST'])
@login_required
def update_about_profile():
    if not is_admin_user():
        flash('Only the admin account can edit the About page.', 'error')
        return redirect(url_for('dashboard'))

    try:
        save_about_profile(request.form.to_dict())
        flash('About page content updated successfully.', 'success')
    except Exception as exc:
        flash(f'Could not update About page content: {exc}', 'error')
    return redirect(url_for('about_editor'))


@app.route('/dashboard/about')
@login_required
def about_editor():
    if not is_admin_user():
        flash('Only the admin account can edit the About page.', 'error')
        return redirect(url_for('dashboard'))

    return render_template(
        'about_editor.html',
        current_user=get_current_user(),
        about_data=get_about_page_data(),
    )


@app.route('/dashboard/timeline', methods=['GET', 'POST'])
@login_required
def timeline_editor():
    if not is_admin_user():
        flash('Only the admin account can edit the timeline.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            saved_id = save_timeline_item(request.form.to_dict())
            flash('Timeline item saved successfully.', 'success')
            return redirect(url_for('timeline_editor', item_id=saved_id))
        except Exception as exc:
            flash(f'Could not save timeline item: {exc}', 'error')

    selected_timeline_id = request.args.get('item_id', '').strip()
    return render_template(
        'timeline_editor.html',
        current_user=get_current_user(),
        timeline_items=get_timeline_items(include_inactive=True),
        timeline_editor=get_timeline_item_by_id(selected_timeline_id),
    )


@app.route('/dashboard/timeline/<int:timeline_id>/toggle-publish', methods=['POST'])
@login_required
def toggle_timeline_publish(timeline_id):
    if not is_admin_user():
        flash('Only the admin account can publish timeline content.', 'error')
        return redirect(url_for('dashboard'))

    with sqlite3.connect(DATABASE_PATH) as conn:
        row = conn.execute(
            'SELECT title, is_active FROM about_timeline WHERE id = ?',
            (timeline_id,),
        ).fetchone()
        if not row:
            flash('Timeline item not found.', 'error')
            return redirect(url_for('timeline_editor'))

        new_status = 0 if row[1] else 1
        conn.execute(
            """
            UPDATE about_timeline
            SET is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, timeline_id),
        )

    action = 'published' if new_status else 'unpublished'
    flash(f'{row[0]} {action} successfully.', 'success')
    return redirect(url_for('timeline_editor', item_id=timeline_id))


@app.route('/dashboard/works', methods=['GET', 'POST'])
@login_required
def works_editor():
    if not is_admin_user():
        flash('Only the admin account can edit Works content.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            save_work_item(request.form.to_dict())
            flash('Work item saved successfully.', 'success')
            return redirect(url_for('works_editor'))
        except Exception as exc:
            flash(f'Could not save work item: {exc}', 'error')

    selected_work_id = request.args.get('work_id', '').strip()
    return render_template(
        'works_editor.html',
        current_user=get_current_user(),
        work_items=get_portfolio_projects(include_inactive=True),
        work_editor=get_portfolio_project_by_id(selected_work_id),
    )


@app.route('/dashboard/works/<int:project_id>/toggle-publish', methods=['POST'])
@login_required
def toggle_work_publish(project_id):
    if not is_admin_user():
        flash('Only the admin account can publish Works content.', 'error')
        return redirect(url_for('dashboard'))

    with sqlite3.connect(DATABASE_PATH) as conn:
        row = conn.execute(
            'SELECT title, is_active FROM about_projects WHERE id = ?',
            (project_id,),
        ).fetchone()
        if not row:
            flash('Work item not found.', 'error')
            return redirect(url_for('works_editor'))

        new_status = 0 if row[1] else 1
        conn.execute(
            """
            UPDATE about_projects
            SET is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, project_id),
        )

    action = 'published' if new_status else 'unpublished'
    flash(f'{row[0]} {action} successfully.', 'success')
    return redirect(url_for('works_editor'))


@app.route('/dashboard/smtp-settings', methods=['GET', 'POST'])
@login_required
def smtp_settings():
    settings = get_smtp_settings() or {}

    if request.method == 'POST':
        try:
            save_smtp_settings(request.form.to_dict())
            flash('SMTP settings saved successfully.', 'success')
            return redirect(url_for('smtp_settings'))
        except Exception:
            flash('Could not save SMTP settings.', 'error')

    settings = get_smtp_settings() or {}
    return render_template(
        'smtp_settings.html',
        current_user=get_current_user(),
        settings=settings,
    )


@app.route('/dashboard/contacts')
@login_required
def contacts():
    contact_rows = get_contacts()
    return render_template(
        'contacts.html',
        current_user=get_current_user(),
        contacts=contact_rows,
    )


@app.route('/dashboard/expenses', methods=['GET'])
@login_required
def expenses():
    selected_month = normalize_month_key(request.args.get("month"))
    expense_data = get_expense_overview(selected_month)
    return render_template(
        'expenses.html',
        current_user=get_current_user(),
        expense_data=expense_data,
        expense_users=get_expense_users(),
        expense_months=get_available_expense_months(selected_month),
        selected_month=selected_month,
        now_date=date.today().isoformat(),
    )


@app.route('/dashboard/expenses/add', methods=['POST'])
@login_required
def add_expense_entry():
    try:
        selected_month = normalize_month_key(request.form.get("selected_month"))
        save_transaction(get_current_user_id(), request.form.to_dict())
        flash('Expense tracker entry saved.', 'success')
    except Exception as exc:
        flash(f'Could not save entry: {exc}', 'error')
    return redirect(url_for('expenses', month=selected_month))


@app.route('/dashboard/contacts/<int:contact_id>')
@login_required
def contact_detail(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('contacts'))

    if not contact.get('is_read'):
        mark_contact_read(contact_id)
        contact = get_contact(contact_id) or contact

    return render_template(
        'contact_detail.html',
        current_user=get_current_user(),
        contact=contact,
    )


@app.route('/dashboard/contacts/<int:contact_id>/toggle-read', methods=['POST'])
@login_required
def toggle_contact_read(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('contacts'))

    new_value = 0 if contact.get('is_read') else 1
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE contacts
            SET is_read = ?,
                read_at = CASE WHEN ? = 1 THEN COALESCE(read_at, CURRENT_TIMESTAMP) ELSE NULL END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_value, new_value, contact_id),
        )

    flash('Contact read status updated.', 'success')
    return redirect(url_for('contacts'))


@app.route('/dashboard/contacts/<int:contact_id>/send-reply', methods=['POST'])
@login_required
def send_contact_reply(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('contacts'))

    reply_subject = request.form.get('reply_subject', '').strip() or f"Re: {contact['subject']}"
    reply_body = request.form.get('reply_message', '').strip()
    if not reply_body:
        flash('Reply message cannot be empty.', 'error')
        return redirect(url_for('contact_detail', contact_id=contact_id))

    try:
        send_reply_to_contact(contact, reply_subject, reply_body)
        update_contact_delivery_status(
            contact_id,
            staff_sent=True,
            staff_error='',
            staff_at=datetime.now(timezone.utc).astimezone().isoformat(sep=' ', timespec='seconds'),
        )
        flash('Reply sent successfully.', 'success')
    except Exception as exc:
        update_contact_delivery_status(
            contact_id,
            staff_sent=False,
            staff_error=str(exc),
        )
        flash(f'Could not send reply: {exc}', 'error')

    return redirect(url_for('contact_detail', contact_id=contact_id))


@app.route('/dashboard/smtp-settings/test-email', methods=['POST'])
@login_required
def test_smtp_email():
    payload = request.get_json(silent=True) or {}
    recipient = payload.get('recipient', '').strip()
    smtp_data = {
        'host': payload.get('host', ''),
        'port': payload.get('port', 465),
        'encryption': payload.get('encryption', 'SSL'),
        'username': payload.get('username', ''),
        'password': payload.get('password', ''),
        'from_name': payload.get('from_name', ''),
        'from_address': payload.get('from_address', ''),
        'timeout_sec': payload.get('timeout_sec', 60),
    }

    try:
        send_test_email(smtp_data, recipient)
        return {'ok': True, 'message': f'Test email sent to {recipient}.'}
    except Exception as exc:
        return {'ok': False, 'message': f'Failed to send test email: {exc}'}, 400


@app.route('/submit_form', methods=['POST', 'GET'])
def submit_form():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            contact_id = save_contact_submission(data)

            smtp_settings_row = get_smtp_settings()
            if smtp_settings_row and int(smtp_settings_row.get("is_active", 1)) == 1:
                contact = {
                    "email": data["email"].strip(),
                    "subject": data["subject"].strip(),
                    "message": data["message"].strip(),
                }

                owner_error = ''
                auto_error = ''
                owner_sent = False
                auto_sent = False

                try:
                    send_smtp_email(
                        smtp_settings_row,
                        OWNER_NOTIFY_EMAIL,
                        f"New contact form message: {contact['subject']}",
                        build_contact_email_text(contact),
                        build_contact_email_html(contact),
                        reply_to=contact["email"],
                    )
                    owner_sent = True
                except Exception as exc:
                    owner_error = str(exc)

                try:
                    send_smtp_email(
                        smtp_settings_row,
                        contact["email"],
                        "Thanks for contacting Tanjilur Rahman",
                        build_auto_reply_text(contact),
                        build_auto_reply_html(contact),
                        reply_to=OWNER_NOTIFY_EMAIL,
                    )
                    auto_sent = True
                except Exception as exc:
                    auto_error = str(exc)

                update_contact_delivery_status(
                    contact_id,
                    owner_sent=owner_sent,
                    auto_sent=auto_sent,
                    owner_error=owner_error,
                    auto_error=auto_error,
                )
            else:
                update_contact_delivery_status(
                    contact_id,
                    owner_sent=False,
                    auto_sent=False,
                    owner_error="SMTP settings are inactive or missing.",
                    auto_error="SMTP settings are inactive or missing.",
                )

            return redirect('/thankyou.html')
        except Exception:
            return 'did not save to database'
    else:
        return 'something went wrong. Try again'
    

    

# @app.route('/components.html')
# def components():
#     return render_template('components.html')

 
# @app.route('/contact.html')
# def contact_jim():
#     return render_template('contact.html')

# @app.route('/works.html')
# def work():
#     return render_template('works.html')

# @app.route('/works')
# def works_jim():
#     return render_template('works.html')

