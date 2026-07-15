---
name: calibration-subgroup-planner
description: Builds per-level working documents needed to run an engineering performance calibration subgroup meeting - one Agenda (with time window and attendee requirements) and one Discussion Template (per-employee rating/feedback sheet) for each level (IC3, IC4, IC5, etc.), based on Squarespace's Calibration Subgroup Playbook. Use this skill whenever the user wants to plan, schedule, or prep for a calibration/leveling/rating subgroup meeting, mentions "calibration subgroup", "IC2/IC3/IC4/IC5 calibration", or asks to turn a roster of employees + levels into a calibration agenda or discussion doc. Also use if the user wants to define who needs to attend conversations for a given level (e.g. "who needs to be in IC4 discussions").
---

# Calibration Subgroup Planner

Turns a roster of employees (with levels) plus a set of attendance rules into
ready-to-use documents for a calibration subgroup meeting — **one combined
document per level** (built from that level's `agenda_IC3.md` +
`discussion_template_IC3.md`, `agenda_IC4.md` + `discussion_template_IC4.md`,
etc., presented as a single document with the Agenda section followed by the
Discussion Template section), so each level can still be shared and scheduled
independently of the others:

1. **Agenda** (per level) — that level's time window (in one or more
   timezones), roster, who needs to attend, and notes on why it landed on the
   date it did.
2. **Discussion Template** (per level) — the rating/feedback capture sheet
   used during that level's session (one summary table + one per-employee
   block asking "What did you rate them and why — in one sentence?",
   "Were you wavering, and if so, why?", and Group Feedback - mirroring the
   Guide's own discussion questions).

This encodes the process from the Calibration Subgroup Playbook: IC2–IC5 are
discussed in subgroups (M5+ goes to a separate session), ~5 minutes per person
(+2 minutes buffer) is the default, and there's a first-5-10-minutes review of
the Process Guide plus a mid-session break.

**Design principle — calibrate across managers, not within one manager's team.**
Sessions are organized **per level** (one time-block per level: IC3, then IC4,
then IC5, etc.), and every session for a level is attended by _all_ managers who
have a report at that level, together. This is deliberate: the point of
calibration is to compare ratings across managers at the same level, not to let
one manager rate their own team in isolation. Managers are therefore
auto-derived from the roster (the `manager` field on each employee) — never ask
the user to re-list managers as attendees. Only ask about _extra_, non-manager
attendees that can't be derived from the roster (Director, Staff Engineer rep,
HRBP/Senior Leader, etc).

**A level is ATOMIC — it never splits across days or sessions.** The whole
point is calibrating the full cohort at a level against each other in one
sitting; a level either runs in full (everyone in it, all required attendees
present) on a given candidate date, or it doesn't run that day at all and
waits for one where it can. The scheduler enforces this itself — it will never
partially schedule a level. If no candidate date has enough time AND everyone
available at once, that level comes back as unscheduled with a clear reason,
rather than being silently split. Don't design around fitting "as many people
as possible" per day; design around finding a day where the _whole_ level fits.

## When to use this

- "Build me a calibration agenda for these 12 engineers"
- "Make a discussion template for IC3/IC4 calibrations on the 10th"
- "Who needs to be in the room for IC4 conversations vs IC2?"
- Any request to schedule or prep materials for a leveling/rating/calibration
  subgroup meeting.

## Step 1 — Gather the inputs

You need three kinds of information. If the user hasn't given all of it, ask —
but keep it to what's actually missing; don't re-ask for things already stated.

**a) Logistics**

- Meeting title / team label
- The daily meeting window — this can be a single local time (e.g. "9am–5pm
  Dublin") or, when the group spans regions, two absolute clock times in two
  different timezones (e.g. "starts 9am EST, must finish by 5:30pm IST"). Don't
  assume a fixed hour gap between timezones — the real gap shifts by an hour or
  two across the year because different countries change their clocks on
  different dates, so always compute it for the actual date(s) used (the
  script handles this; don't do the arithmetic by hand)
- One or more **candidate dates**, in preference order — if a level doesn't
  fit (time-wise or availability-wise) on the earliest date, the whole level
  (never a partial slice of it) rolls to the next candidate date. Ask for a
  few candidate dates up front so you don't have to go back and forth
- Which timezone(s) to display in the table (defaults to the window's own
  timezones if not specified)
- Minutes per person (default 5) and buffer minutes (default 0 — ask if they
  want a buffer; the playbook mentions "5 mins per person, +2 if needed" but
  don't assume it)
- Where to put breaks (e.g. after IC3 and after IC4)

**b) The roster**
For each employee: name, manager, team, level (IC2–IC5), and optionally length
of service and time in position (used in the Discussion Template), and any
dates they're unavailable. If the user gives you a spreadsheet, doc, or pasted
list, parse it into this shape rather than asking them to retype it. If the
data includes levels outside IC2–IC5 (e.g. IC6/Staff, M5+/manager levels),
confirm whether those are in scope before including them — the playbook's
subgroup process is specifically IC2–IC5, with M5+ handled separately.

**c) Who else needs to be in the room, per level**
Managers are automatically included as attendees for any level where they have a
report (derived straight from the roster) — don't ask about this part. What you
do need from the user is any _extra_, non-manager attendee per level — e.g.:

- IC3: + staff engineer rep
- IC4: + staff engineer rep, director
- IC5: + director, + whoever handles the M5+/HRBP cross-check (per the
  playbook's HBR step)

If the user only specifies extra attendees for some levels, leave the others
blank rather than guessing — flag it back to them so it's obvious in the Agenda.

Also flag if the roster spans a large number of people/managers — 5+7 minutes
per person adds up fast (e.g. 38 people ≈ 4.5 hours), so it's worth confirming
whether they want it split across multiple days or just want to see the real
total length.

**d) Availability / time off for the candidate dates**
Before finalizing `unavailable_dates` for each employee, check real calendar
availability if a calendar tool is connected, rather than just asking the user
to hand-type a list:

- Collect the distinct set of people who actually need to be free that day:
  every manager appearing in the roster for that date's levels, plus (if you
  have their emails) the employees themselves.
- Use `Google Calendar:suggest_time` with those people's emails, the candidate
  dates as the search interval, and `preferences` constrained to the day's
  actual local working hours, to see whether a free slot covering the whole
  session exists. This directly answers "is everyone free that day" without
  you reasoning about individual events.
- To check a _specific_ person's availability (e.g. "is Doug out on the 12th"),
  use `Google Calendar:list_events` on their calendar (their email as
  `calendarId`) filtered to `eventType: ["OUT_OF_OFFICE"]` for the candidate
  date range — an all-day or day-spanning OOO event there means that manager's
  reports should be marked unavailable for that date.
- These are read-only calls — no need to ask permission before checking.
- If a person's calendar isn't visible to you (no access, wrong email, or the
  tool isn't connected), don't guess — ask the user directly for that person's
  availability rather than silently assuming they're free.
- Translate whatever you find into the right field: an individual out is
  `unavailable_dates` on their employee object; a _manager_ out (blocking
  their whole team's session that day) is `manager_unavailable_dates`; a
  required non-manager attendee out (e.g. a specific Director who must be in
  every IC4/IC5 session) is `extra_attendee_unavailable_dates`. Tell the user
  which dates you ruled out for whom and why, so they can correct you if the
  calendar data is stale or wrong.

Optionally also ask which employees should be flagged for a longer discussion
(e.g. non-3 ratings, open questions) — the playbook's own feedback notes say
these should get priority time and everyone else should move faster. This is
just a flag (marked with `(*)` in the agenda), not a reordering — let the
human decide the actual running order.

**Promotion consideration gets its own, separate buffer.** Anyone being
considered for promotion should be marked `"promo_consideration": true` on
their employee object — this automatically adds an extra `promo_buffer_minutes`
(default 3) on top of their normal slot, and marks them `[Promo]` in the
Agenda. Ask the user which employees (if any) are promo cases; don't guess
based on tenure or rating.

## Step 2 — Build the input JSON

Assemble everything from Step 1 into a JSON file matching the shape in
`references/example_input.json`. Key fields:

- `window_start` / `window_end`: each `{"time": "HH:MM", "tz": "IANA/Zone"}` —
  these are two absolute clock times, possibly in different timezones (e.g.
  window_start in `America/New_York`, window_end in `Europe/Dublin`). The
  script computes the real gap between them for each candidate date.
- `candidate_dates`: ordered list of `YYYY-MM-DD` dates to try, in preference
  order. The scheduler tries to fit each level (whole and unsplit) into the
  first date's remaining window; if it can't, that level rolls entirely to
  the next candidate date.
- `display_timezones`: list of `{"label": ..., "tz": ...}` — the label is what
  shows in the table header
- `level_order`: the order levels are scheduled in (e.g. `["IC2","IC3","IC4","IC5"]`)
- `break_after_levels`: which level(s) get a break immediately after they
  finish (only inserted if there's more work left that day)
- `level_attendees`: map of level → list of _extra_ (non-manager) attendee
  labels/names. Managers don't go here — they're derived automatically from
  each employee's `manager` field.
- `employees`: list of employee objects, each with a `manager` field (drives
  roster grouping and attendee lists), optionally `unavailable_dates` (dates
  that employee can't attend — from Step 1d — since levels are atomic, even
  one unavailable person blocks the whole level from running that day), and
  optionally `promo_consideration: true` for anyone up for promotion (adds
  the extra promo buffer and an `[Promo]` marker)
- `manager_unavailable_dates`: map of manager name → dates _the manager
  themselves_ is out (not their reports). Since a manager must be present for
  their own reports' discussion, this is treated as if all of that manager's
  reports were unavailable that date too.
- `extra_attendee_unavailable_dates`: map of a named/required non-manager
  attendee (as it appears in `level_attendees`, e.g. `"Director"` or a named
  person) → dates they're out. Because that attendee is required for the
  _whole_ level's session, the entire level is skipped for that date rather
  than partially scheduled.
- `promo_buffer_minutes`: extra minutes added on top of a person's normal slot
  when `promo_consideration` is true (default 3 — this is separate from the
  general `buffer_minutes_per_person`, which applies to everyone)

## Step 3 — Run the scheduler

Run the bundled script to compute time windows deterministically (don't do the
timezone/offset math yourself — DST and multi-timezone arithmetic is easy to
get subtly wrong by hand):

```bash
python3 scripts/build_schedule.py <input.json> --outdir <workdir>
```

This writes **one Agenda and one Discussion Template file per level** into
`<workdir>` — e.g. `agenda_IC3.md` + `discussion_template_IC3.md`,
`agenda_IC4.md` + `discussion_template_IC4.md`, and so on. These two files
per level are intermediate output from the script; when presenting to the
user (Step 4), combine each level's pair into ONE document (Agenda section
followed by Discussion Template section) rather than presenting them as two
separate documents. Each level's combined document is still fully
self-contained (its own header, its own scheduling notes) so levels can be
shared with different audiences or scheduled independently without anyone
seeing another level's roster. The script prints the full set of output
paths per level as JSON.

Write this instruction as a Guide just before the Discussion Template section of each doc - do not change any wording:
When introducing each person, keep your summary to 30 seconds. Use this format:
"[Name] is a [level]. I've rated them [4 — Exceptional / 3 — Strong / 2 — Gaps / 1 — Not Meeting] because [one sentence — what they delivered or where the gap is, anchored to what's expected at their level]. I'm [confident / this one was close]."
Example:
"Alex is an IC4. I've rated them 3 — Strong Contribution. They own their squad's backend reliability work end to end, consistently deliver without direction, and their peers rely on them for cross-team coordination. That's what I expect from a solid IC4. I'm confident on this one."
Compare that to an 4 — Exceptional Contribution at IC4: Alex would need to be raising the bar for the team, not just meeting it — proactively removing blockers, expanding scope beyond what was asked. They're not there yet, and that's not a criticism — 3 — Strong Contribution is a genuinely strong result.
A reminder of what this is not:
This is not a performance review recap. We are not covering everything this person accomplished this half. We are not reading from their self-review. We are answering three questions:
What level are they?
What did you rate them and why — in one sentence?
Were you wavering, and if so, why?
If the room has no questions and the rating is R3 — Strong Contribution, we move on.

## Step 4 — Present as Artifacts

For each level, combine that level's `agenda_{level}.md` and
`discussion_template_{level}.md` into ONE document (Agenda section, then
Discussion Template section) and create a single Claude Artifact (markdown)
from it, titled clearly by level, e.g. `IC3 Calibration Subgroup`, `IC4
Calibration Subgroup`, etc. Do not present the Agenda and Discussion
Template as two separate Artifacts/documents.

Show them to the user in the conversation. Briefly point out:

- Which date each level landed on
- Each level's own "Scheduling notes" section, which explains why it couldn't
  run on earlier candidate dates (manager/attendee unavailability, not enough
  time) and confirms which date it was fully scheduled on
- Any level the script couldn't schedule at all because it ran out of
  candidate dates (offer to add more dates, resolve a conflict, or free up
  more window time)
- Any levels where attendee requirements weren't specified
- Any employees flagged for a longer discussion

Offer to adjust anything (minutes per person, break placement, attendee lists,
adding/removing employees) and re-run the script rather than hand-editing the
markdown, since re-running keeps the times and per-level files consistent.

## Notes from the playbook worth surfacing to the user

These are recurring pieces of feedback from past calibration cycles — mention
them when relevant, don't just silently bake them in:

- Use a visible on-screen timer per candidate; the 5-minute limit is
  frequently not enforced in practice and sessions run long.
- Prioritize non-3 ratings / promo cases / open questions earlier in the
  agenda; don't spend equal time on people with no pushback on their rating.
- Make sure everyone scheduled is actually covered, including people who
  received a 3 (these are sometimes skipped when time runs short).
- Pre-reading anonymized summaries in advance speeds up the actual meeting.
- Smaller subgroups (vs. one large org-wide meeting) are preferred, but keep
  a consistent set of managers across all subgroups for calibration
  consistency.
