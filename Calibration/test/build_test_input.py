#!/usr/bin/env python3
"""Builds a fabricated-but-realistic roster input JSON for testing the
discussion-order design. All names, managers, teams, and ratings are made
up - not drawn from any real roster - specifically so this test fixture
never contains real employee data. Includes rating-1 and rating-2 examples
(absent from earlier real-data test runs) so the sensitive_review path is
actually exercised."""
import json

# (name, manager, team, level, rating, promo, needs_snr_leader_discussion, los_yrs, tip_yrs)
ROWS = [
    ("Devon Ashford", "Morgan Reyes", "Platform", "IC2", 3, False, False, 0.4, None),

    ("Avery Lin", "Taylor Brooks", "Checkout", "IC3", 3, False, False, 1.5, None),
    ("Reese Palmer", "Riley Foster", "Infra", "IC3", 3, False, False, 0.3, None),
    ("Quinn Delgado", "Drew Sullivan", "Growth", "IC3", 3, False, False, 2.4, 0.9),
    ("Sawyer Kim", "Drew Sullivan", "Growth", "IC3", 3, False, False, 0.9, None),
    ("Rowan Ibarra", "Casey Nguyen", "Data", "IC3", 3, False, False, 2.1, 0.9),
    ("Elliot Marsh", "Casey Nguyen", "Data", "IC3", 4, True, False, 3.0, None),
    ("Finley Osei", "Jamie Chen", "Billing", "IC3", 4, True, False, 3.4, None),
    ("Harlow Bennett", "Morgan Reyes", "Platform", "IC3", 4, True, True, 3.3, 1.9),
    ("Marlowe Cruz", "Riley Foster", "Infra", "IC3", 3, False, False, 0.5, None),
    ("Kai Whitfield", "Morgan Reyes", "Platform", "IC3", 3, False, False, 0.8, None),
    ("Sage Donovan", "Taylor Brooks", "Checkout", "IC3", 3, False, False, 0.3, None),

    ("Emerson Vaughn", "Taylor Brooks", "Checkout", "IC4", 4, True, False, 4.0, None),
    ("Peyton Alcaraz", "Casey Nguyen", "Data", "IC4", 4, True, False, 3.3, None),
    ("Tatum Whitmore", "Casey Nguyen", "Data", "IC4", 4, True, False, 5.1, None),
    ("Briar Solis", "Jamie Chen", "Billing", "IC4", 4, True, False, 4.6, 3.3),
    ("Micah Ostrander", "Riley Foster", "Infra", "IC4", 4, False, True, 0.6, None),
    ("Landry Cho", "Taylor Brooks", "Checkout", "IC4", 3, False, False, 5.8, None),
    ("Dallas Feldman", "Drew Sullivan", "Growth", "IC4", 3, False, False, 0.2, None),
    ("Emory Castellano", "Casey Nguyen", "Data", "IC4", 2, False, False, 2.0, None),
    ("Wren Abernathy", "Riley Foster", "Infra", "IC4", 3, False, False, 0.6, None),
    ("Sutton Kavanagh", "Morgan Reyes", "Platform", "IC4", 3, False, False, 6.4, 2.4),
    ("Blair Okafor", "Morgan Reyes", "Platform", "IC4", 3, False, False, 0.6, None),
    ("Marin Delacroix", "Jamie Chen", "Billing", "IC4", 1, False, True, 4.6, None),

    ("Phoenix Larkspur", "Jamie Chen", "Billing", "IC5", 4, False, False, 4.0, None),
    ("Wilder Novak", "Casey Nguyen", "Data", "IC5", 3, False, False, 1.8, None),
    ("Aspen Torres", "Casey Nguyen", "Data", "IC5", 3, False, False, 4.5, 2.9),
    ("Marlow Higgins", "Riley Foster", "Infra", "IC5", 3, False, False, 5.8, None),
    ("Story Beaumont", "Riley Foster", "Infra", "IC5", 3, False, False, 3.5, 1.9),
    ("Ellery Pruitt", "Drew Sullivan", "Growth", "IC5", 3, False, False, 7.6, None),
    ("Bellamy Osgood", "Drew Sullivan", "Growth", "IC5", 3, False, False, 4.1, None),
    ("Indigo Faulkner", "Drew Sullivan", "Growth", "IC5", 3, False, True, 3.6, 1.4),
    ("Juniper Slate", "Taylor Brooks", "Checkout", "IC5", 3, False, False, 4.1, None),
    ("Ashby Renwick", "Taylor Brooks", "Checkout", "IC5", 3, False, False, 4.6, None),
    ("Cricket Vandermeer", "Taylor Brooks", "Checkout", "IC5", 3, False, False, 5.7, 2.9),
    ("Wells Ashworth", "Taylor Brooks", "Checkout", "IC5", 3, False, False, 8.1, None),
    ("Merritt Calloway", "Taylor Brooks", "Checkout", "IC5", 3, False, False, 3.9, 2.9),

    ("Morgan Reyes", "Harper Voss", "Platform", "M5", 3, False, False, 4.3, 2.4),
    ("Jamie Chen", "Harper Voss", "Billing", "M5", 3, False, False, 0.3, None),
    ("Taylor Brooks", "Logan Pierce", "Checkout", "M5", 3, False, False, 6.7, 2.3),
    ("Casey Nguyen", "Logan Pierce", "Data", "M5", 3, False, False, 4.6, 1.3),
    ("Drew Sullivan", "Harper Voss", "Growth", "M5", 3, False, False, 0.6, None),
    ("Riley Foster", "Logan Pierce", "Infra", "M5", 3, False, False, 4.4, 1.4),
    ("Skyler Vance", "Harper Voss", "Platform", "M5", 3, False, False, 7.8, 2.9),
]

employees = []
for name, manager, team, level, rating, promo, needs_snr, los, tip in ROWS:
    e = {
        "name": name,
        "manager": manager,
        "team": team,
        "level": level,
        "manager_proposed_rating": rating,
        "promo_consideration": promo,
        "needs_snr_leader_discussion": needs_snr,
        "length_of_service_yrs": los,
    }
    if tip is not None:
        e["time_in_position_yrs"] = tip
    employees.append(e)

data = {
    "meeting_title": "Fabricated Test Calibration Subgroup",
    "team_label": "Multiple teams (cross-manager calibration) - FABRICATED TEST DATA, no real employees",
    "window_start": {"time": "09:00", "tz": "America/New_York"},
    "window_end": {"time": "17:30", "tz": "Europe/Dublin"},
    "candidate_dates": ["2026-08-18", "2026-08-19", "2026-08-20"],
    "display_timezones": [
        {"label": "EST", "tz": "America/New_York"},
        {"label": "IST", "tz": "Europe/Dublin"},
    ],
    "minutes_per_person": 5,
    "buffer_minutes_per_person": 0,
    "promo_buffer_minutes": 3,
    "break_minutes": 10,
    "break_after_levels": ["IC3", "IC4", "IC5"],
    "level_order": ["IC2", "IC3", "IC4", "IC5", "M5"],
    "notetaker": "TBD",
    "level_attendees": {},
    "manager_unavailable_dates": {},
    "extra_attendee_unavailable_dates": {},
    "employees": employees,
}

with open("roster_input.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Wrote roster_input.json with {len(employees)} fabricated employees")
