"""Skill Analysis Module.

Loads the skill knowledge base and provides gap analysis between a
student's current skills and the requirements for a target career role.
"""
from __future__ import annotations

import json
import os
from typing import Any

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skill_graph.json")


def load_knowledge_base(path: str = _DATA_PATH) -> dict[str, Any]:
    """Load the skill knowledge base from a JSON file."""
    with open(os.path.normpath(path), encoding="utf-8") as fh:
        return json.load(fh)


def normalise_skill(skill: str, all_skills: list[str]) -> str | None:
    """Return the canonical skill name matching *skill* (case-insensitive).

    Returns ``None`` if the skill is not found in the knowledge base.
    """
    skill_lower = skill.strip().lower()
    for s in all_skills:
        if s.lower() == skill_lower:
            return s
    return None


def analyse_skills(
    known_skills: list[str],
    target_role: str,
    kb: dict[str, Any],
) -> dict[str, Any]:
    """Perform gap analysis for *known_skills* against *target_role*.

    Returns a dict with:
    - ``known``: validated known skills
    - ``required``: skills required for the role
    - ``optional``: optional/bonus skills for the role
    - ``missing_required``: required skills the student still needs
    - ``missing_optional``: optional skills the student still needs
    - ``readiness_score``: percentage of required skills already known (0–100)
    - ``role_description``: description of the target role
    - ``adjacent``: skills closely related to known skills but not yet known
    """
    all_skills: list[str] = list(kb["skills"].keys())
    career_paths: dict[str, Any] = kb.get("career_paths", {})
    dependencies: dict[str, list[str]] = kb.get("dependencies", {})

    # Normalise known skills against the knowledge base
    validated_known: list[str] = []
    for s in known_skills:
        canonical = normalise_skill(s, all_skills)
        if canonical and canonical not in validated_known:
            validated_known.append(canonical)

    # Retrieve role information
    role_info = career_paths.get(target_role, {})
    required: list[str] = role_info.get("required_skills", [])
    optional: list[str] = role_info.get("optional_skills", [])
    role_description: str = role_info.get("description", "")

    missing_required = [s for s in required if s not in validated_known]
    missing_optional = [s for s in optional if s not in validated_known]

    readiness_score = 0.0
    if required:
        readiness_score = round(
            (len(required) - len(missing_required)) / len(required) * 100, 1
        )

    # Adjacent skills: skills for which the student satisfies ALL prerequisites
    known_set = set(validated_known)
    adjacent: list[str] = []
    for skill, prereqs in dependencies.items():
        if skill in known_set:
            continue
        if prereqs and all(p in known_set for p in prereqs):
            adjacent.append(skill)

    return {
        "known": validated_known,
        "required": required,
        "optional": optional,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "readiness_score": readiness_score,
        "role_description": role_description,
        "adjacent": adjacent,
    }


def get_skill_info(skill: str, kb: dict[str, Any]) -> dict[str, str]:
    """Return metadata for a single skill from the knowledge base."""
    return kb["skills"].get(skill, {})


def list_career_roles(kb: dict[str, Any]) -> list[str]:
    """Return the list of available career roles."""
    return list(kb.get("career_paths", {}).keys())


def list_all_skills(kb: dict[str, Any]) -> list[str]:
    """Return all skill names in the knowledge base."""
    return list(kb.get("skills", {}).keys())
