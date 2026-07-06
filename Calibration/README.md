# Calibration Subgroup Planner — README

This skill is designed to implement the Calibrations playbook located here: https://docs.google.com/document/d/1rpD_1YYFJWhsrXDMAU0b1IV9_Qc9JyywKhQ911kpvLQ/edit?tab=t.0

A Claude skill that turns a roster + a few scheduling rules into ready-to-run
calibration session documents: one combined **Agenda + Discussion Template**
per level (IC3, IC4, IC5, etc.), showing exactly who's discussed, when, and
who needs to be in the room, followed by the rating sheet to fill out live.

## Installing it

Upload the `.skill` file in Claude (Settings → Skills, or drag it into a
chat). Once installed, just describe what you need in plain language — you
don't need to mention the skill by name.

## What to say to trigger it

Anything like:

- "Build me a calibration agenda for these engineers"
- "Make a discussion template for our IC3/IC4 calibrations"
- "Who needs to be in the room for IC4 conversations?"
- Paste in a roster (spreadsheet, doc, CSV) and ask for an agenda

## What to have ready

You don't need all of this up front — Claude will ask for what's missing —
but having it ready speeds things up:

1. **The roster** — paste a spreadsheet/CSV/doc and it'll be parsed
   automatically. Per person, the skill can use:
   - **Name** (required)
   - **Manager** (required — drives grouping and auto-adds them as an attendee)
   - **Team**
   - **Level** (IC2–IC5 — required, determines which session they're in)
   - **Length of service** (years) — shown in the Discussion Template
   - **Time in position** (years) — shown in the Discussion Template
   - **Being put forward for promotion?** (yes/no) — adds a few extra minutes
     to their slot automatically and flags them `[Promo]` in the Agenda and
     "Yes" in the Discussion Template's Promo Proposal column
   - **Flagged for a longer discussion** (yes/no) — e.g. a non-3 rating or an
     open question; marks them `(*)` so the group knows to expect more time,
     without actually reordering anyone
   - **Needs a senior leader discussion** (yes/no) — flows into the Discussion
     Template's "Needs Snr Leader Discussion" column
   - **Unavailable dates** — any dates that person can't attend
2. **Logistics** — a meeting window (e.g. "9am–5pm Dublin," or "starts 9am
   EST, must finish by 5:30pm IST" for multi-region groups), and a few
   **candidate dates** in order of preference.
3. **Extra attendees per level** — anyone required beyond the managers
   themselves (managers are added automatically), e.g. a Staff Engineer rep
   for IC3/IC4, a Director for IC4/IC5.
4. **Anyone with a scheduling conflict** — people, or whole managers, who are
   out on certain dates. If you have a calendar connected, Claude will check
   it directly rather than asking you to type this out.

## What you get back

**One document per level**, combining both parts in order:

- **Agenda section** — one row per candidate with their exact time slot (in
  whichever timezones you need), grouped by manager, plus who's required to
  attend and why the session landed on the date it did.
- **Discussion Template section** — the rating capture sheet: one summary
  table (manager/team/level/ratings/promo flag) plus a Strengths /
  Opportunities / Group Feedback block per person.

Ask for them as chat artifacts, or ask Claude to save them straight into a
Google Drive folder as Google Docs (landscape, ready to fill in).

## The rules baked in (so you don't have to repeat them)

- **Cross-manager calibration.** Every session at a level includes _all_
  managers with a report at that level, together — the point is comparing
  people across managers, not letting one manager rate their own team alone.
- **Sessions are atomic.** A level runs in full on one date — the whole
  cohort, all required attendees — or it doesn't run that day at all. It's
  never split into "10 of 12 today, 2 more later."
- **Real timezone math.** If your window spans two timezones (e.g. EST +
  IST), the actual time gap is computed per calendar date, not assumed —
  the US and other regions don't always shift clocks on the same day.
- **Automatic conflict handling.** If a required manager, employee, or extra
  attendee is unavailable on a candidate date, that whole level waits for a
  date that works — and if it can't find one, you get a clear explanation of
  why, not a silently broken schedule.

## Iterating

Just tell Claude what to change — "push the deadline out," "John's out all
of August too," "add a promo flag for Jane" — and it'll re-run the scheduler
with the update rather than hand-editing anything, so the times stay
consistent.

## Known limitations

- **Google Docs dropdown chips** (the native `@Dropdown` picker) can't be
  created through the API — rating cells come with a `▾ Select 1–4`
  placeholder instead. You need to use the GEMINI_PROMPT.md https://github.com/sdoran-sqsp/management-skills/blob/main/Calibration/GEMINI_PROMPT.md skill within the Google Doc to finalise formatting.
- Calendar-based availability checking only works as well as the calendar
  access Claude has — if it can't see someone's calendar, it'll ask you
  rather than guess.
