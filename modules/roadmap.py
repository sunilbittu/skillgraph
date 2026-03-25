"""Roadmap Module.

Generates a milestone-based weekly learning plan from skill recommendations.
"""
from __future__ import annotations

import math
from typing import Any


_HOURS_PER_WEEK = 10  # assumed study hours per week

_EFFORT_HOURS = {
    "beginner": 8,
    "intermediate": 20,
    "advanced": 40,
}


def _weeks_for_skill(skill: str, kb: dict[str, Any]) -> int:
    """Estimate the number of weeks required to learn *skill*."""
    level = kb.get("skills", {}).get(skill, {}).get("level", "intermediate")
    hours = _EFFORT_HOURS.get(level, 20)
    return max(1, math.ceil(hours / _HOURS_PER_WEEK))


def generate_roadmap(
    recommendations: list[dict[str, str]],
    kb: dict[str, Any],
    weeks_per_phase: int = 4,
) -> list[dict[str, Any]]:
    """Return a list of learning phases (milestones).

    Each phase is a dict with:
    - ``phase``: integer phase number (1-based)
    - ``label``: human-readable label, e.g. ``"Phase 1 – Foundation (Weeks 1–4)"``
    - ``skills``: list of skill names in this phase
    - ``start_week``: first week of the phase
    - ``end_week``: last week of the phase
    - ``priority``: overall priority of the phase (High / Medium / Low)
    """
    if not recommendations:
        return []

    # Separate high-priority from medium/low
    high = [r for r in recommendations if r.get("priority") == "High"]
    medium = [r for r in recommendations if r.get("priority") != "High"]

    phases: list[dict[str, Any]] = []
    week_cursor = 1

    for group_idx, group in enumerate([high, medium], start=1):
        if not group:
            continue

        # Chunk the group into phases of roughly `weeks_per_phase` weeks
        phase_skills: list[str] = []
        phase_weeks = 0
        phase_priority = "High" if group_idx == 1 else "Medium"

        for rec in group:
            skill = rec["skill"]
            w = _weeks_for_skill(skill, kb)
            if phase_weeks + w > weeks_per_phase and phase_skills:
                # Flush current phase
                phases.append(
                    _make_phase(len(phases) + 1, phase_skills, week_cursor, week_cursor + phase_weeks - 1, phase_priority)
                )
                week_cursor += phase_weeks
                phase_skills = [skill]
                phase_weeks = w
            else:
                phase_skills.append(skill)
                phase_weeks += w

        if phase_skills:
            phases.append(
                _make_phase(len(phases) + 1, phase_skills, week_cursor, week_cursor + phase_weeks - 1, phase_priority)
            )
            week_cursor += phase_weeks

    return phases


def _make_phase(
    number: int,
    skills: list[str],
    start: int,
    end: int,
    priority: str,
) -> dict[str, Any]:
    label_map = {1: "Foundation", 2: "Core Skills", 3: "Advanced", 4: "Specialisation"}
    label_suffix = label_map.get(number, f"Phase {number}")
    return {
        "phase": number,
        "label": f"Phase {number} – {label_suffix} (Weeks {start}–{end})",
        "skills": skills,
        "start_week": start,
        "end_week": end,
        "priority": priority,
    }


def roadmap_to_dataframe(phases: list[dict[str, Any]]) -> "Any":
    """Convert the roadmap list to a Pandas DataFrame for display."""
    import pandas as pd  # type: ignore[import-untyped]

    rows = []
    for phase in phases:
        for skill in phase["skills"]:
            rows.append(
                {
                    "Phase": phase["label"],
                    "Skill": skill,
                    "Weeks": f"{phase['start_week']}–{phase['end_week']}",
                    "Priority": phase["priority"],
                }
            )
    return pd.DataFrame(rows)
