_#!/usr/bin/env python3
"""
Builds a calibration subgroup Agenda and Discussion Template from a JSON input file.

Usage:
    python3 build_schedule.py input.json --outdir /path/to/outdir

Input JSON shape (see references/example_input.json for a full example):
{
  "meeting_title": "Commerce Engineering Calibration Subgroup",
  "team_label": "Commerce Engineering (multiple managers - cross-manager calibration)",
  "window_start": {"time": "09:00", "tz": "America/New_York"},
  "window_end":   {"time": "17:30", "tz": "Europe/Dublin"},
  "candidate_dates": ["2026-08-11", "2026-08-12", "2026-08-13"],
  "display_timezones": [
    {"label": "EST", "tz": "America/New_York"},
    {"label": "IST", "tz": "Europe/Dublin"}
  ],
  "minutes_per_person": 5,
  "buffer_minutes_per_person": 0,
  "break_minutes": 10,
  "break_after_levels": ["IC3", "IC4"],
  "level_order": ["IC2", "IC3", "IC4", "IC5"],
  "level_attendees": {
    "IC3": ["Staff Engineer rep"],
    "IC4": ["Staff Engineer rep", "Director"],
    "IC5": ["Director", "Senior Leader"]
  },
  "notetaker": "TBD",
  "manager_unavailable_dates": {
    "Scott Koenig": ["2026-07-30", "2026-07-31"]
  },
  "extra_attendee_unavailable_dates": {
    "Director": ["2026-08-03", "2026-08-04"]
  },
  "employees": [
    {
      "name": "Jane Doe",
      "manager": "Sam Manager",
      "team": "Checkout",
      "level": "IC3",
      "length_of_service_yrs": 2.5,
      "time_in_position_yrs": 1,
      "needs_snr_leader_discussion": false,
      "flag_longer_discussion": false,
      "unavailable_dates": ["2026-08-12"]
    }
  ]
}

Notes:
- The daily meeting window is defined by TWO absolute clock times in two (possibly
  different) timezones: `window_start` (e.g. "9am EST/EDT, wherever that lands local
  time") and `window_end` (e.g. "5:30pm Irish time, whatever the actual offset is that
  day"). The real gap between these varies by a couple of hours across the year because
  the US and Ireland don't shift their clocks on exactly the same dates - this script
  computes the true gap per calendar date via `zoneinfo`, rather than assuming a fixed
  offset.
- Scheduling is done PER LEVEL, across as many `candidate_dates` as needed. Within a
  level, employees are grouped by manager (so a level's session is naturally attended by
  every manager with a report at that level - the point is cross-manager calibration,
  not letting one manager rate their own team in isolation). Managers are auto-derived
  from the `manager` field - do not list "Manager"/"Skip-level manager" in
  `level_attendees`; that field is for EXTRA, non-manager attendees only.
- EVERY LEVEL IS ATOMIC. A level either runs in full on a given candidate date (the
  entire cohort, all required attendees present, enough time left in the window) or it
  doesn't run that day at all - it is NEVER partially scheduled. This is deliberate:
  calibration means comparing the whole cohort at a level side by side, so splitting a
  level across sessions would defeat the purpose. If a level can't fit today, the whole
  thing rolls to the next candidate date, not just the overflow.
- `unavailable_dates` on an employee excludes them from being scheduled that date -
  since the level is atomic, even ONE unavailable person in that level blocks the WHOLE
  level from running that day, not just that person.
- `manager_unavailable_dates` is for when the MANAGER themselves is out (not their
  reports) - since a manager must be present for their reports' discussion, this blocks
  the whole level (for that manager's reports) the same way an unavailable employee does.
- `extra_attendee_unavailable_dates` is for named/required non-manager attendees (e.g. a
  specific Director or HRBP listed in `level_attendees`) being out. Because that
  attendee is required for the WHOLE level's session, it blocks the whole level for that
  date too.
- If `candidate_dates` runs out before a level can find a date where it fits AND
  everyone's available, the script reports it as unscheduled with the specific reasons
  it failed on each date it tried, so the user can supply more dates, resolve a
  conflict, or free up more time per day rather than content silently vanishing or
  silently splitting.
- "flag_longer_discussion" employees (e.g. non-3 ratings, open questions) are noted with
  a (*) in the agenda roster - the tool does NOT reorder people, since managers usually
  want to control discussion order themselves.
"""
import json
import argparse
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from collections import defaultdict


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("input_json")
    p.add_argument("--outdir", default=".")
    return p.parse_args()


def fmt(dt):
    s = dt.strftime("%I:%M %p").lstrip("0").lower()
    return s


def group_by_manager(emps):
    """Group employees by manager, sorted alphabetically by manager then name."""
    by_manager = defaultdict(list)
    for e in emps:
        by_manager[e.get("manager", "Unassigned")].append(e)
    grouped = []
    for manager in sorted(by_manager.keys()):
        members = sorted(by_manager[manager], key=lambda e: e["name"])
        grouped.append((manager, members))
    return grouped


def person_minutes(e, data):
    """Minutes allotted to one employee's discussion, including any promo buffer."""
    base = data.get("minutes_per_person", 5) + data.get("buffer_minutes_per_person", 0)
    if e.get("promo_consideration"):
        base += data.get("promo_buffer_minutes", 3)
    return base


def compute_window_utc(date_str, window_start, window_end):
    """Given a calendar date and two {time, tz} specs, return (start_utc, end_utc)."""
    tz1 = ZoneInfo(window_start["tz"])
    hh1, mm1 = map(int, window_start["time"].split(":"))
    start_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=hh1, minute=mm1, tzinfo=tz1)

    tz2 = ZoneInfo(window_end["tz"])
    hh2, mm2 = map(int, window_end["time"].split(":"))
    end_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=hh2, minute=mm2, tzinfo=tz2)

    return start_dt.astimezone(timezone.utc), end_dt.astimezone(timezone.utc)


def to_display_windows(start_utc, end_utc, display_tzs):
    windows = {}
    for tzinfo in display_tzs:
        tz = ZoneInfo(tzinfo["tz"])
        windows[tzinfo["label"]] = (fmt(start_utc.astimezone(tz)), fmt(end_utc.astimezone(tz)))
    return windows


def build_schedule(data):
    window_start = data["window_start"]
    window_end = data["window_end"]
    candidate_dates = data["candidate_dates"]
    break_minutes = data.get("break_minutes", 10)
    break_after_levels = set(data.get("break_after_levels", []))
    level_order = data["level_order"]
    level_attendees_extra = data.get("level_attendees", {})
    manager_unavailable = data.get("manager_unavailable_dates", {})
    attendee_unavailable = data.get("extra_attendee_unavailable_dates", {})
    display_tzs = data.get("display_timezones", [{"label": "Local", "tz": window_start["tz"]}])

    # Pending queue per level, manager-grouped for a readable roster. Each level is
    # scheduled as ONE atomic block - it either runs in full on a given day (everyone
    # who's in it, together) or it doesn't run that day at all. This is deliberate: the
    # point of calibration is comparing the whole cohort at a level side by side, so a
    # level must never be split across sessions just because part of it happened to fit.
    pending = {}
    for level in level_order:
        emps = [e for e in data.get("employees", []) if e["level"] == level]
        ordered = []
        for manager, members in group_by_manager(emps):
            ordered.extend(members)
        pending[level] = ordered

    days = []
    skipped_dates = []
    diagnostics = defaultdict(list)  # level -> [(date, reason)] for every date it couldn't run

    for date_str in candidate_dates:
        start_utc, end_utc = compute_window_utc(date_str, window_start, window_end)
        if end_utc <= start_utc:
            skipped_dates.append(date_str)
            continue

        cursor = start_utc
        remaining = (end_utc - start_utc).total_seconds() / 60.0
        day_blocks = []

        for level in level_order:
            full_emps = pending[level]
            if not full_emps:
                continue

            managers_needed = sorted({e.get("manager", "Unassigned") for e in full_emps})
            extras_today = level_attendees_extra.get(level, [])

            blocked_managers = [m for m in managers_needed if date_str in manager_unavailable.get(m, [])]
            blocked_employees = [e["name"] for e in full_emps if date_str in e.get("unavailable_dates", [])]
            blocked_extras = [a for a in extras_today if date_str in attendee_unavailable.get(a, [])]

            if blocked_managers or blocked_employees or blocked_extras:
                reasons = []
                if blocked_managers:
                    reasons.append(f"manager(s) unavailable: {', '.join(blocked_managers)}")
                if blocked_employees:
                    reasons.append(f"employee(s) unavailable: {', '.join(blocked_employees)}")
                if blocked_extras:
                    reasons.append(f"required attendee(s) unavailable: {', '.join(blocked_extras)}")
                diagnostics[level].append((date_str, "; ".join(reasons)))
                continue

            time_needed = sum(person_minutes(e, data) for e in full_emps)
            if time_needed > remaining + 1e-9:
                diagnostics[level].append(
                    (date_str, f"not enough time left that day (needs {int(round(time_needed))} min, "
                               f"{int(round(remaining))} min left)")
                )
                continue

            # Everyone's available and it fits - schedule the WHOLE level now.
            block_start, block_end = cursor, cursor + timedelta(minutes=time_needed)
            windows = to_display_windows(block_start, block_end, display_tzs)
            attendees = managers_needed + extras_today

            day_blocks.append({
                "type": "level",
                "level": level,
                "employees": full_emps,
                "count": len(full_emps),
                "windows": windows,
                "attendees": attendees,
            })
            pending[level] = []
            cursor, remaining = block_end, remaining - time_needed

            more_pending_elsewhere = any(pending[l] for l in level_order)
            if level in break_after_levels and more_pending_elsewhere and remaining >= break_minutes:
                bstart, bend = cursor, cursor + timedelta(minutes=break_minutes)
                bwindows = to_display_windows(bstart, bend, display_tzs)
                day_blocks.append({"type": "break", "windows": bwindows})
                cursor, remaining = bend, remaining - break_minutes

            if remaining <= 0:
                break

        if day_blocks:
            days.append({"date": date_str, "blocks": day_blocks})

        if not any(pending[l] for l in level_order):
            break

    leftover = {l: pending[l] for l in level_order if pending[l]}
    return days, leftover, skipped_dates, diagnostics


def compress_dates(date_strs):
    """Turn ['2026-08-04','2026-08-05','2026-08-06'] into 'Aug 4–Aug 6'."""
    dates = sorted(datetime.strptime(d, "%Y-%m-%d").date() for d in date_strs)
    ranges = []
    start = prev = dates[0]
    for d in dates[1:]:
        if (d - prev).days == 1:
            prev = d
            continue
        ranges.append((start, prev))
        start = prev = d
    ranges.append((start, prev))
    parts = []
    for s, e in ranges:
        if s == e:
            parts.append(s.strftime("%b %-d"))
        else:
            parts.append(f"{s.strftime('%b %-d')}–{e.strftime('%b %-d')}")
    return ", ".join(parts)


def render_agenda_for_level(data, level, days, leftover, skipped_dates, diagnostics):
    """One self-contained Agenda document for a single level's session."""
    tz_labels = [t["label"] for t in data.get("display_timezones", [{"label": "Local"}])]
    lines = []
    lines.append(f"# Calibration Subgroup Agenda — {level}")
    lines.append("")
    lines.append(f"**{data.get('meeting_title', 'Calibration Subgroup')}**")
    lines.append("")
    if data.get("team_label"):
        lines.append(f"**Team(s):** {data['team_label']}")
        lines.append("")
    ws, we = data["window_start"], data["window_end"]
    lines.append(f"**Daily window:** {ws['time']} {ws['tz']} start, no later than {we['time']} {we['tz']} finish  ")
    lines.append(f"**Notetaker:** {data.get('notetaker', 'TBD')}  ")
    timer_str = f"{data.get('minutes_per_person', 5)} mins per person"
    if data.get("buffer_minutes_per_person"):
        timer_str += f" (+{data['buffer_minutes_per_person']} if needed)"
    promo_buffer = data.get("promo_buffer_minutes", 3)
    timer_str += f", +{promo_buffer} min extra for anyone being considered for promotion"
    lines.append(f"**Timer:** {timer_str}")
    lines.append("")
    lines.append(f"_This is the {level} session only — a separate document exists for each "
                 "level so they can be shared/scheduled independently. Every manager with a "
                 "report at this level attends together, along with the full cohort being "
                 "discussed, all in one sitting — the whole point is calibrating everyone at "
                 f"{level} against each other in one go._")
    lines.append("")

    header = ["Roster", "# Discussions"] + tz_labels + ["Attendees required"]

    any_flagged = False
    any_promo = False
    found_date = None
    found_block = None
    for day in days:
        for block in day["blocks"]:
            if block.get("type") == "level" and block["level"] == level:
                found_date, found_block = day["date"], block
                break
        if found_block:
            break

    if found_block:
        lines.append(f"## {found_date}")
        lines.append("")
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join([":-:"] * len(header)) + "|")

        roster_lines = []
        for manager, members in group_by_manager(found_block["employees"]):
            roster_lines.append(f"**{manager}:**")
            for e in members:
                marker = ""
                if e.get("flag_longer_discussion"):
                    marker += " (*)"
                    any_flagged = True
                if e.get("promo_consideration"):
                    marker += " [Promo]"
                    any_promo = True
                roster_lines.append(f"- {e['name']}{marker}")
        roster_cell = "<br>".join(roster_lines)
        windows_cells = [f"{found_block['windows'][l][0]} – {found_block['windows'][l][1]}" for l in tz_labels]
        attendees_cell = "<br>".join(found_block["attendees"]) if found_block["attendees"] else ""
        row = [roster_cell, str(found_block["count"])] + windows_cells + [attendees_cell]
        lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    else:
        lines.append("## Not yet scheduled")
        lines.append("")

    # Scheduling notes for just this level.
    grouped = defaultdict(list)
    for date_str, reason in diagnostics.get(level, []):
        grouped[reason].append(date_str)
    if grouped or level in leftover:
        lines.append("## Scheduling notes")
        lines.append("")
        for reason, dates in grouped.items():
            lines.append(f"- Could not run {compress_dates(dates)} — {reason}")
        if found_block:
            lines.append(f"- ✅ Scheduled in full on **{found_date}**")
        elif level in leftover:
            lines.append("- ⚠️ **Not scheduled** — ran out of candidate dates with everyone "
                          "available at once. Add more candidate dates, resolve the "
                          "conflicts above, or free up more time per day.")
        lines.append("")

    if skipped_dates:
        lines.append(f"⚠️ **Skipped candidate date(s) with an invalid window:** {', '.join(skipped_dates)} "
                     "(the finish time landed before the start time in these timezones on that date).")
        lines.append("")

    if any_flagged:
        lines.append("_(*) flagged for a longer discussion (e.g. non-3 rating, open question) — plan extra time._")
        lines.append("")

    if any_promo:
        lines.append(f"_[Promo] being considered for promotion — includes an extra {promo_buffer} min buffer in their slot._")
        lines.append("")

    lines.append("## Process reminders (from the playbook)")
    lines.append("- Spend the first 5–10 minutes reviewing the Process Guide and today's agenda with the group.")
    lines.append("- Use a visible on-screen timer per candidate discussion.")
    lines.append("- Focus on the distribution curve — don't exhaustively discuss people with no pushback on their rating.")
    lines.append("- Make sure everyone is covered, including people who received a 3.")
    lines.append("")
    return "\n".join(lines)


def render_discussion_template_for_level(data, level, days):
    """One self-contained Discussion Template document for a single level."""
    emps = []
    for day in days:
        for block in day["blocks"]:
            if block.get("type") == "level" and block["level"] == level:
                emps = block["employees"]

    lines = []
    lines.append(f"# Calibration Subgroup Discussion Template — {level}")
    lines.append("")
    lines.append(f"**{data.get('meeting_title', 'Calibration Subgroup')}**")
    lines.append("")
    lines.append(f"**Notetaker:** {data.get('notetaker', 'TBD')}  ")
    timer_str = f"{data.get('minutes_per_person', 5)} mins per person"
    if data.get("buffer_minutes_per_person"):
        timer_str += f" (+{data['buffer_minutes_per_person']} if needed)"
    promo_buffer = data.get("promo_buffer_minutes", 3)
    timer_str += f", +{promo_buffer} min extra for anyone being considered for promotion"
    lines.append(f"**Timer:** {timer_str}")
    lines.append("")

    if not emps:
        lines.append("_This level hasn't been scheduled yet — see the matching Agenda document._")
        lines.append("")
        return "\n".join(lines)

    header = ["Employee", "Manager", "Team", "Job Level", "Manager Proposed Rating",
               "Group Proposed Rating", "Promo Proposal (link)", "Needs Snr Leader Discussion",
               "Length of Service (yrs)", "Time in Position (yrs)"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join([":-:"] * len(header)) + "|")
    for e in emps:
        row = [
            e["name"],
            e.get("manager", ""),
            e.get("team", ""),
            e["level"],
            "Not selected",
            "Not selected",
            "Yes" if e.get("promo_consideration") else "",
            "Yes" if e.get("needs_snr_leader_discussion") else "Not selected",
            str(e.get("length_of_service_yrs", "")),
            str(e.get("time_in_position_yrs", "")),
        ]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    for e in emps:
        lines.append(f"### {e['name']}")
        lines.append("")
        lines.append("| Strengths | Opportunities |")
        lines.append("|:-:|:-:|")
        lines.append("| - <br>- <br>- | - <br>- <br>- |")
        lines.append("")
        lines.append("**Group Feedback:** ")
        lines.append("")

    return "\n".join(lines)


def main():
    args = parse_args()
    with open(args.input_json) as f:
        data = json.load(f)

    days, leftover, skipped_dates, diagnostics = build_schedule(data)

    os.makedirs(args.outdir, exist_ok=True)
    outputs = {}
    for level in data["level_order"]:
        has_employees = any(e["level"] == level for e in data.get("employees", []))
        if not has_employees:
            continue

        agenda_md = render_agenda_for_level(data, level, days, leftover, skipped_dates, diagnostics)
        discussion_md = render_discussion_template_for_level(data, level, days)

        agenda_path = os.path.join(args.outdir, f"agenda_{level}.md")
        discussion_path = os.path.join(args.outdir, f"discussion_template_{level}.md")
        with open(agenda_path, "w") as f:
            f.write(agenda_md)
        with open(discussion_path, "w") as f:
            f.write(discussion_md)

        outputs[level] = {"agenda": agenda_path, "discussion_template": discussion_path}

    print(json.dumps({
        "outputs": outputs,
        "days_used": len(days),
        "leftover": {k: [e["name"] for e in v] for k, v in leftover.items()},
    }))


if __name__ == "__main__":
    main()