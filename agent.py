"""
agent.py  —  GenAPAC Workspace Assistant
=========================================
Multi-agent productivity assistant built for the
Gen AI Academy APAC Hackathon (Google Cloud × H2S).

Stack : google-adk 1.14.0 · Gemini 2.5 Flash · Google Cloud Datastore (genapac)
Author: Abin
"""

import os
import datetime
import logging

from dotenv import load_dotenv
import google.cloud.logging
from google.cloud import datastore

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

# ─────────────────────────────────────────────
# 1.  BOOTSTRAP
# ─────────────────────────────────────────────
load_dotenv()

try:
    google.cloud.logging.Client().setup_logging()
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

MODEL   = os.getenv("MODEL", "gemini-2.5-flash")
API_KEY = os.getenv("GOOGLE_API_KEY", "")          # passed automatically by ADK runtime

# ─────────────────────────────────────────────
# 2.  DATASTORE CLIENT  (database = "genapac")
# ─────────────────────────────────────────────
db = datastore.Client(
    project=os.getenv("PROJECT_ID", "genapachack"),
    database="genapac",
)

# ─────────────────────────────────────────────
# 3.  TOOLS
# ─────────────────────────────────────────────

# ── TASKS ────────────────────────────────────

def add_task(title: str, priority: str = "medium", due_date: str = "") -> str:
    """
    Add a new task to the workspace.

    Args:
        title:    Short description of the task.
        priority: low | medium | high  (default: medium)
        due_date: Optional due date, YYYY-MM-DD format.

    Returns:
        Confirmation string with the new task ID.
    """
    try:
        key  = db.key("Task")
        task = datastore.Entity(key=key)
        task.update({
            "title":      title,
            "completed":  False,
            "priority":   priority,
            "due_date":   due_date,
            "created_at": datetime.datetime.utcnow(),
        })
        db.put(task)
        return f"✅ Task added — '{title}' | priority: {priority} | ID: {task.key.id}"
    except Exception as e:
        logger.error("add_task: %s", e)
        return f"Error: {e}"


def list_tasks(filter_status: str = "all") -> str:
    """
    List tasks from the workspace.

    Args:
        filter_status: all | pending | completed

    Returns:
        Formatted task list.
    """
    try:
        query = db.query(kind="Task")
        if filter_status == "pending":
            query.add_filter("completed", "=", False)
        elif filter_status == "completed":
            query.add_filter("completed", "=", True)

        tasks = list(query.fetch())
        if not tasks:
            return "📋 No tasks found."

        lines = [f"📋 Tasks ({filter_status}):"]
        for t in tasks:
            icon     = "✅" if t.get("completed") else "⏳"
            priority = t.get("priority", "medium").upper()
            due      = f"  due: {t['due_date']}" if t.get("due_date") else ""
            lines.append(f"  {icon} [{priority}] {t.get('title')}{due}  (ID: {t.key.id})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def complete_task(task_id: str) -> str:
    """
    Mark a task as completed.

    Args:
        task_id: The numeric ID of the task to complete.

    Returns:
        Confirmation or error message.
    """
    try:
        nid  = int("".join(filter(str.isdigit, task_id)))
        key  = db.key("Task", nid)
        task = db.get(key)
        if not task:
            return f"⚠️ Task {nid} not found."
        task["completed"]    = True
        task["completed_at"] = datetime.datetime.utcnow()
        db.put(task)
        return f"✅ Task {nid} marked complete."
    except Exception as e:
        return f"Error: {e}"


def delete_task(task_id: str) -> str:
    """
    Permanently delete a task.

    Args:
        task_id: The numeric ID of the task to delete.

    Returns:
        Confirmation or error message.
    """
    try:
        nid  = int("".join(filter(str.isdigit, task_id)))
        key  = db.key("Task", nid)
        if db.get(key):
            db.delete(key)
            return f"🗑️ Task {nid} deleted."
        return f"⚠️ Task {nid} not found."
    except Exception as e:
        return f"Error: {e}"


def update_task(task_id: str, new_title: str = "",
                new_priority: str = "", new_due_date: str = "") -> str:
    """
    Update an existing task's fields.

    Args:
        task_id:      Numeric task ID.
        new_title:    Replacement title (leave blank to keep current).
        new_priority: Replacement priority (leave blank to keep current).
        new_due_date: Replacement due date YYYY-MM-DD (leave blank to keep current).

    Returns:
        Confirmation or error message.
    """
    try:
        nid  = int("".join(filter(str.isdigit, task_id)))
        key  = db.key("Task", nid)
        task = db.get(key)
        if not task:
            return f"⚠️ Task {nid} not found."
        if new_title:    task["title"]    = new_title
        if new_priority: task["priority"] = new_priority
        if new_due_date: task["due_date"] = new_due_date
        task["updated_at"] = datetime.datetime.utcnow()
        db.put(task)
        return f"✏️ Task {nid} updated."
    except Exception as e:
        return f"Error: {e}"


# ── NOTES ────────────────────────────────────

def add_note(title: str, content: str, tags: str = "") -> str:
    """
    Save a detailed note.

    Args:
        title:   Short title for the note.
        content: Full body text of the note.
        tags:    Comma-separated tags, e.g. 'work,ideas'.

    Returns:
        Confirmation string with the new note ID.
    """
    try:
        key  = db.key("Note")
        note = datastore.Entity(key=key)
        note.update({
            "title":      title,
            "content":    content,
            "tags":       tags,
            "created_at": datetime.datetime.utcnow(),
        })
        db.put(note)
        return f"📝 Note saved — '{title}' | ID: {note.key.id}"
    except Exception as e:
        return f"Error: {e}"


def list_notes(tag_filter: str = "") -> str:
    """
    List all saved notes, optionally filtered by tag.

    Args:
        tag_filter: Only return notes that include this tag (leave blank for all).

    Returns:
        Formatted note list with previews.
    """
    try:
        notes = list(db.query(kind="Note").fetch())
        if not notes:
            return "📓 No notes found."
        if tag_filter:
            notes = [n for n in notes if tag_filter.lower() in n.get("tags", "").lower()]
            if not notes:
                return f"📓 No notes tagged '{tag_filter}'."
        lines = [f"📓 Notes{' [#' + tag_filter + ']' if tag_filter else ''}:"]
        for n in notes:
            preview  = n.get("content", "")[:55]
            preview  = (preview + "…") if len(n.get("content", "")) > 55 else preview
            tag_str  = f"  #{n['tags']}" if n.get("tags") else ""
            lines.append(f"  • [{n.key.id}] {n.get('title')}{tag_str} — {preview}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def get_note(note_id: str) -> str:
    """
    Retrieve the full content of a note.

    Args:
        note_id: The numeric ID of the note.

    Returns:
        Full note title and content.
    """
    try:
        nid  = int("".join(filter(str.isdigit, note_id)))
        note = db.get(db.key("Note", nid))
        if not note:
            return f"⚠️ Note {nid} not found."
        return (
            f"📝 {note.get('title')}\n"
            f"Tags: {note.get('tags') or 'none'}  |  Created: {note.get('created_at')}\n"
            f"{'─'*40}\n"
            f"{note.get('content')}"
        )
    except Exception as e:
        return f"Error: {e}"


def delete_note(note_id: str) -> str:
    """
    Delete a note permanently.

    Args:
        note_id: The numeric ID of the note to delete.

    Returns:
        Confirmation or error message.
    """
    try:
        nid = int("".join(filter(str.isdigit, note_id)))
        key = db.key("Note", nid)
        if db.get(key):
            db.delete(key)
            return f"🗑️ Note {nid} deleted."
        return f"⚠️ Note {nid} not found."
    except Exception as e:
        return f"Error: {e}"


# ── CALENDAR ─────────────────────────────────

def add_calendar_event(title: str, date: str, time: str = "",
                       description: str = "", location: str = "") -> str:
    """
    Schedule a calendar event.

    Args:
        title:       Event name.
        date:        Date in YYYY-MM-DD format.
        time:        Optional time in HH:MM (24-hour) format.
        description: Optional details about the event.
        location:    Optional venue or meeting link.

    Returns:
        Confirmation with event ID.
    """
    try:
        key   = db.key("CalendarEvent")
        event = datastore.Entity(key=key)
        event.update({
            "title":       title,
            "date":        date,
            "time":        time,
            "description": description,
            "location":    location,
            "created_at":  datetime.datetime.utcnow(),
        })
        db.put(event)
        time_str = f" at {time}" if time else ""
        loc_str  = f" @ {location}" if location else ""
        return f"📅 Event scheduled — '{title}' on {date}{time_str}{loc_str} | ID: {event.key.id}"
    except Exception as e:
        return f"Error: {e}"


def list_calendar_events(from_date: str = "", to_date: str = "") -> str:
    """
    List calendar events, optionally within a date range.

    Args:
        from_date: Start of range in YYYY-MM-DD (leave blank for all past and future).
        to_date:   End of range in YYYY-MM-DD (leave blank for no upper limit).

    Returns:
        Formatted event list sorted by date.
    """
    try:
        query        = db.query(kind="CalendarEvent")
        query.order  = ["date"]
        events       = list(query.fetch())
        if not events:
            return "📅 No events found."
        if from_date:
            events = [e for e in events if e.get("date", "") >= from_date]
        if to_date:
            events = [e for e in events if e.get("date", "") <= to_date]
        if not events:
            return "📅 No events in that date range."
        lines = ["📅 Calendar Events:"]
        for e in events:
            time_str = f" {e['time']}" if e.get("time") else ""
            loc_str  = f"  @ {e['location']}" if e.get("location") else ""
            lines.append(f"  • [{e.key.id}] {e.get('date')}{time_str} — {e.get('title')}{loc_str}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def delete_calendar_event(event_id: str) -> str:
    """
    Delete a calendar event.

    Args:
        event_id: Numeric ID of the event to delete.

    Returns:
        Confirmation or error message.
    """
    try:
        nid = int("".join(filter(str.isdigit, event_id)))
        key = db.key("CalendarEvent", nid)
        if db.get(key):
            db.delete(key)
            return f"🗑️ Event {nid} deleted."
        return f"⚠️ Event {nid} not found."
    except Exception as e:
        return f"Error: {e}"


def update_calendar_event(event_id: str, new_title: str = "", new_date: str = "",
                          new_time: str = "", new_location: str = "") -> str:
    """
    Update an existing calendar event.

    Args:
        event_id:     Numeric event ID.
        new_title:    Replacement title (leave blank to keep current).
        new_date:     Replacement date YYYY-MM-DD (leave blank to keep current).
        new_time:     Replacement time HH:MM (leave blank to keep current).
        new_location: Replacement location (leave blank to keep current).

    Returns:
        Confirmation or error message.
    """
    try:
        nid   = int("".join(filter(str.isdigit, event_id)))
        key   = db.key("CalendarEvent", nid)
        event = db.get(key)
        if not event:
            return f"⚠️ Event {nid} not found."
        if new_title:    event["title"]    = new_title
        if new_date:     event["date"]     = new_date
        if new_time:     event["time"]     = new_time
        if new_location: event["location"] = new_location
        event["updated_at"] = datetime.datetime.utcnow()
        db.put(event)
        return f"✏️ Event {nid} updated."
    except Exception as e:
        return f"Error: {e}"


# ── REMINDERS ────────────────────────────────

def add_reminder(message: str, remind_at: str) -> str:
    """
    Set a reminder.

    Args:
        message:   What to be reminded about.
        remind_at: ISO-8601 datetime string, e.g. '2025-12-31T09:00:00'.

    Returns:
        Confirmation with reminder ID.
    """
    try:
        key      = db.key("Reminder")
        reminder = datastore.Entity(key=key)
        reminder.update({
            "message":    message,
            "remind_at":  remind_at,
            "triggered":  False,
            "created_at": datetime.datetime.utcnow(),
        })
        db.put(reminder)
        return f"🔔 Reminder set — '{message}' at {remind_at} | ID: {reminder.key.id}"
    except Exception as e:
        return f"Error: {e}"


def list_reminders() -> str:
    """
    List all pending (not yet triggered) reminders.

    Returns:
        Formatted list of upcoming reminders.
    """
    try:
        reminders = list(db.query(kind="Reminder").fetch())
        pending   = [r for r in reminders if not r.get("triggered")]
        if not pending:
            return "🔔 No pending reminders."
        lines = ["🔔 Pending Reminders:"]
        for r in pending:
            lines.append(f"  • [{r.key.id}] {r.get('remind_at')} — {r.get('message')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ── WORKSPACE SUMMARY ────────────────────────

def workspace_summary() -> str:
    """
    Return a high-level dashboard of the entire workspace:
    pending tasks, upcoming calendar events, and recent notes.

    Returns:
        Formatted multi-section summary string.
    """
    try:
        # Pending tasks
        tq = db.query(kind="Task")
        tq.add_filter("completed", "=", False)
        pending = list(tq.fetch())

        # Upcoming events (today onwards)
        today  = datetime.date.today().isoformat()
        eq     = db.query(kind="CalendarEvent")
        eq.order = ["date"]
        upcoming = [e for e in eq.fetch() if e.get("date", "") >= today][:5]

        # Last 3 notes
        notes = list(db.query(kind="Note").fetch())[-3:]

        lines = ["🗂️  Workspace Summary", "═" * 32]

        lines.append(f"\n📋 Pending Tasks ({len(pending)}):")
        if pending:
            for t in pending[:5]:
                due = f"  due {t['due_date']}" if t.get("due_date") else ""
                lines.append(f"  ⏳ [{t.get('priority','?').upper()}] {t.get('title')}{due}  (ID: {t.key.id})")
            if len(pending) > 5:
                lines.append(f"  … and {len(pending) - 5} more")
        else:
            lines.append("  🎉 All tasks complete!")

        lines.append(f"\n📅 Upcoming Events ({len(upcoming)}):")
        if upcoming:
            for e in upcoming:
                ts = f" {e['time']}" if e.get("time") else ""
                lines.append(f"  • {e.get('date')}{ts} — {e.get('title')}")
        else:
            lines.append("  No upcoming events.")

        lines.append(f"\n📓 Recent Notes ({len(notes)}):")
        if notes:
            for n in notes:
                lines.append(f"  • {n.get('title')}  (ID: {n.key.id})")
        else:
            lines.append("  No notes yet.")

        return "\n".join(lines)
    except Exception as e:
        return f"Error generating summary: {e}"


# ─────────────────────────────────────────────
# 4.  AGENT STATE BRIDGE
# ─────────────────────────────────────────────

def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict:
    """
    Internal routing tool — stores the raw user prompt into shared agent state
    so the workspace_agent can access it.

    Args:
        prompt: The original user message.

    Returns:
        Status dict.
    """
    tool_context.state["PROMPT"] = prompt
    return {"status": "ok"}


# ─────────────────────────────────────────────
# 5.  AGENT INSTRUCTIONS
# ─────────────────────────────────────────────

def workspace_instruction(ctx) -> str:
    user_prompt = ctx.state.get("PROMPT", "Greet the user warmly.")
    today_str   = datetime.date.today().isoformat()
    return f"""
You are the Workspace Executive Assistant built for the
Gen AI Academy APAC Hackathon (GenAPAC · Google Cloud).

Today's date: {today_str}

Your personality: professional, warm, efficient, and proactive.
Always open with a brief friendly greeting, then complete the request.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER REQUEST:  {user_prompt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
1. Use the appropriate tool(s) to fulfil the request.
2. Always report the IDs of any items you create, update, or delete.
3. If the user wants to see data, call the relevant list/get tool — never guess.
4. For ambiguous requests, make a reasonable attempt first, then ask.
5. Format tool output clearly using the emoji labels the tools return.
6. Never fabricate task IDs, note IDs, or event IDs.

AVAILABLE CAPABILITIES:
• Tasks      — add · list · complete · update · delete
• Notes      — add · list · get · delete
• Calendar   — add event · list events · update · delete
• Reminders  — add · list
• Dashboard  — workspace_summary (overview of everything)
"""


def root_instruction(ctx) -> str:
    raw = ctx.state.get("user_input", "Hello")
    return f"""
You are the routing agent. Execute EXACTLY these two steps, in order:

Step 1 — Call 'add_prompt_to_state' with the prompt below.
Step 2 — Immediately hand off to the 'workflow' sub-agent.

Do NOT respond to the user yourself.

PROMPT: {raw}
"""


# ─────────────────────────────────────────────
# 6.  AGENT ASSEMBLY
# ─────────────────────────────────────────────

ALL_TOOLS = [
    # Tasks
    add_task, list_tasks, complete_task, update_task, delete_task,
    # Notes
    add_note, list_notes, get_note, delete_note,
    # Calendar
    add_calendar_event, list_calendar_events, update_calendar_event, delete_calendar_event,
    # Reminders
    add_reminder, list_reminders,
    # Dashboard
    workspace_summary,
]

# Primary worker agent — has access to all tools
workspace_agent = Agent(
    name="workspace",
    model=MODEL,
    instruction=workspace_instruction,
    tools=ALL_TOOLS,
)

# Sequential wrapper (allows chaining more sub-agents later)
workflow = SequentialAgent(
    name="workflow",
    sub_agents=[workspace_agent],
)

# Root / router agent — entry point used by the API runner
root_agent = Agent(
    name="root",
    model=MODEL,
    instruction=root_instruction,
    tools=[add_prompt_to_state],
    sub_agents=[workflow],
)

# ── ADK convention: expose `agent` at package level ──
agent = root_agent