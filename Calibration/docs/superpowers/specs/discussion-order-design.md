# Calibration Discussion Ordering — Design

## Problem

Today, `Calibration/scripts/build_schedule.py` lists each level's roster
grouped by manager, alphabetically, with no other ordering logic. The user
running a calibration session wants the discussion order within a level to
prioritize:

1. Anyone up for promotion.
2. Anyone with a manager-proposed rating of 4 (top tier).
3. Anyone with a manager-proposed rating of 1 or 2 (sensitive — gaps to /
   not meeting expectations) — these should be flagged to the person running
   the skill for review with the People team, but NOT called out in the
   generated documents themselves.
4. Everyone else, grouped by manager (today's existing behavior), so each
   manager can walk through their remaining reports together.

This only affects *display/discussion order* within a level — it does not
change scheduling (which day a level lands on), since that's driven purely by
the total minutes needed for the whole cohort, which is order-independent.

**This is a targeted change to the existing `build_schedule.py`, not a
rewrite.** Every function named below already exists in that file today; the
plan is to modify them in place (new helper + small edits to two render
functions + one docstring/JSON-output addition), not to introduce a parallel
implementation or a new script.

## New input field

Add an optional employee field:

```json
"manager_proposed_rating": 4
```

- Integer 1–4 (4 = best, matching the color scale in `GEMINI_PROMPT.md`:
  Purple-Exceptional=4, Green-Strong=3, Yellow-Gaps=2, Red-Not Meeting=1).
- **Optional.** Calibration prep may start before ratings are finalized.
  Employees with no `manager_proposed_rating`, or a rating of `3`, are treated
  identically — both fall into the "everyone else, grouped by manager" tier.
- This field drives ordering and the sensitive-review flag ONLY. It is never
  used to pre-fill the Discussion Template's "Manager Proposed Rating"
  column — that column always starts as `"Not selected"` regardless of
  whether this input field is present, since the rating is meant to be
  decided/confirmed live in the meeting, not pre-populated from prep data.
  **The tool must never write a value into that column that wasn't
  explicitly provided.**

## Ordering logic — `order_for_discussion(employees)`

A new helper alongside the existing `group_by_manager` in
`build_schedule.py`, used FROM `group_by_manager` (not instead of it — see
below). It replaces the current direct call to `group_by_manager` at the one
call site where `pending[level]` is built inside `build_schedule()`:

```python
# today:
ordered = []
for manager, members in group_by_manager(emps):
    ordered.extend(members)
pending[level] = ordered

# becomes:
pending[level] = order_for_discussion(emps)
```

`order_for_discussion` buckets employees into 4 tiers, in this priority
order, each person landing in exactly the first tier they qualify for:

1. `promo_consideration == True`
2. `manager_proposed_rating == 4`
3. `manager_proposed_rating in (1, 2)` (sensitive)
4. everyone else

Promo takes priority over rating — someone who is both up for promotion and
rated 1/2 appears in tier 1 only, not duplicated. Within each tier, it calls
the existing `group_by_manager(tier_members)` and flattens the result (same
grouping style — alphabetical manager, then alphabetical name — just scoped
to one tier at a time), then concatenates tiers 1→4. `group_by_manager`
itself is unchanged and is still used elsewhere as-is.

A manager with reports in more than one tier (e.g. one promo report and one
ordinary report) simply has their name repeated in the `Manager` column on
two separate rows, at two different points in the table — there's no
sub-header grouping in the corrected per-candidate-row table format (see
Rendering changes below), so this isn't the visual duplication concern it
would have been under the old aggregate-cell rendering.

## Scheduling — no change

`build_schedule`'s atomic per-level scheduling only depends on the *sum* of
per-person minutes for the level (via the existing `person_minutes`), never
on order. `pending[level]`'s order changes, but the date/time-fitting logic
(`compute_window_utc`, the day/level loop, diagnostics) is untouched.

## Rendering changes

- **Agenda table** (`render_agenda_for_level` + `build_schedule`): the
  checked-in script currently renders ONE aggregate row per level (a single
  block start–end span, plus a roster crammed into one cell via
  `group_by_manager`), which is a pre-existing gap independent of the
  ordering work — `person_minutes` (5 min, or 5+3=8 min for
  `promo_consideration`) already drives the *total* block duration, but was
  never used to give each candidate their own row/time. Confirmed against a
  real prior output doc, the correct table format is **one row per
  candidate**, columns `<tz labels...> | Candidate | Manager | Team`, each
  row showing that person's own computed start–end slot — not a single
  lumped span. Fix, in the same two functions already being touched:
  - `build_schedule()`: when a level's block is scheduled, walk
    `full_emps` (now in `order_for_discussion` order) with a running time
    cursor starting at `block_start`, computing each person's own
    `(slot_start, slot_end)` via `person_minutes(e, data)` — 5 min normally,
    8 min if `promo_consideration`. Store this as a new `"slots"` list on
    the block dict: `[{"employee": e, "windows": {...}}, ...]`, alongside
    the existing `"windows"` (still kept, for the overall block span used
    elsewhere) and `"employees"`.
  - `render_agenda_for_level()`: replace the single aggregate roster row
    with one row per entry in `found_block["slots"]`, in order — each row's
    time columns come from that slot's own `windows`, and the
    `Candidate`/`Manager`/`Team` columns come from that slot's employee.
    `(*)` and `[Promo]` markers move onto the `Candidate` cell per row
    (still no rating marker). `"Attendees required"` moves out of the table
    entirely into a `**Attendees required:** ...` line above the table
    (comma-joined), since the reference format doesn't carry it as a
    table column.
  - Because rows are emitted straight from `found_block["slots"]` in
    `order_for_discussion` order, the tiering from this spec (promo →
    rating 4 → sensitive → remaining-by-manager) is exactly what determines
    row order and therefore who gets discussed — and therefore
    scheduled — first. No separate manager sub-header is needed in this
    table format (manager is just a column), so the "repeated manager
    header" cosmetic effect noted earlier does not apply to the Agenda
    table — it only ever applied to the old aggregate-cell rendering, which
    this replaces.
- **Discussion Template** (`render_discussion_template_for_level`): the
  ordering itself needs no structural change — it already iterates the
  block's employee list in whatever order it's given, so the new tiered
  order flows through automatically. The "Manager Proposed Rating" column
  keeps rendering `"Not selected"` unconditionally, regardless of whether
  `manager_proposed_rating` was supplied in the input. Separately, per a
  note added directly to `CALIBRATION-SUB-GROUP.MD`, this function also
  gains a fixed `## Guide` section inserted once, immediately before the
  summary table (after the header, before the `Employee | Manager | ...`
  table) — a verbatim block of guidance text for how the group should
  introduce each candidate (30-second summary format, example, and a
  "what this is not" reminder). This text is copied exactly as written in
  `CALIBRATION-SUB-GROUP.MD` — implementers must not edit its wording. It
  is independent of the tiering/rating work above; it's just additive
  content in the same function. The per-person block further down the same
  function also had its two placeholder columns renamed from generic
  `Strengths | Opportunities` to two of the Guide's own discussion
  questions - `What did you rate them and why — in one sentence?` and
  `Were you wavering, and if so, why?` - so the capture sheet mirrors what
  the Guide actually asks the group to answer, with a single blank cell
  each (no bullet-list placeholder, since these are one-line answers).

## Sensitive-rating callout (chat only, not in documents)

`main()`'s existing JSON summary (currently `outputs` / `days_used` /
`leftover`) gains one new key:

```json
"sensitive_review": {
  "IC4": ["Jordan P.", "Sam T."]
}
```

Listing, per level, the names of anyone with `manager_proposed_rating` of 1
or 2. The script's module docstring gains an explicit instruction that
whoever is driving this script (Claude, reading the docstring to run the
skill) should proactively surface these names to the user in chat for
People team review — and must NOT write them into the generated
Agenda/Discussion Template files, since those documents may be shared more
widely than the immediate conversation.

## Docs & example updates

- `Calibration/README.md`: document `manager_proposed_rating` as an
  optional roster field under "What to have ready", and add the reordering
  rule to "The rules baked in".
- `Calibration/scripts/build_schedule.py` docstring: document the new
  field, the tiering rule, and the chat-callout-not-document instruction, in
  the same style as the existing notes on atomicity/timezone math.
- `Calibration/references/example_input.json`: add at least one rating-4
  and one rating-2 example employee so the sample data exercises the new
  ordering and flag.

## Out of scope

- No change to how ratings are collected, stored, or finalized during the
  actual meeting.
- No new markers/tags added to the rendered documents for rating tiers.
- No change to scheduling/date-fitting logic.
- No new script or parallel implementation — all changes land in the
  existing `build_schedule.py`.
