"""Recommendation Engine.

Generates rule-based skill recommendations and, when an OpenAI API key is
configured, augments them with AI-generated career advice.
"""
from __future__ import annotations

import os
from typing import Any


def _priority_score(skill: str, analysis: dict[str, Any], kb: dict[str, Any]) -> int:
    """Return a sorting priority for a skill (lower = higher priority)."""
    dependencies: dict[str, list[str]] = kb.get("dependencies", {})
    # Skills with fewer remaining prerequisites come first
    prereqs = dependencies.get(skill, [])
    known_set = set(analysis["known"])
    unmet = sum(1 for p in prereqs if p not in known_set)
    return unmet


def generate_recommendations(
    analysis: dict[str, Any],
    kb: dict[str, Any],
    max_items: int = 10,
) -> list[dict[str, str]]:
    """Return an ordered list of recommended skills to learn next.

    Each item is a dict with ``skill``, ``reason``, and ``priority`` keys.
    """
    recommendations: list[dict[str, str]] = []
    known_set = set(analysis["known"])
    skills_meta: dict[str, Any] = kb.get("skills", {})

    # 1. Adjacent unlockable skills (all prerequisites met)
    for skill in analysis["adjacent"]:
        meta = skills_meta.get(skill, {})
        recommendations.append(
            {
                "skill": skill,
                "reason": (
                    f"All prerequisites are met. Start here to unlock more advanced skills. "
                    f"({meta.get('description', '')})"
                ),
                "priority": "High",
            }
        )

    # 2. Missing required skills whose prerequisites are partially met
    missing_required = list(analysis["missing_required"])
    missing_required.sort(
        key=lambda s: _priority_score(s, analysis, kb)
    )
    for skill in missing_required:
        if skill in {r["skill"] for r in recommendations}:
            continue
        meta = skills_meta.get(skill, {})
        recommendations.append(
            {
                "skill": skill,
                "reason": (
                    f"Required for your target role. "
                    f"({meta.get('description', '')})"
                ),
                "priority": "High",
            }
        )

    # 3. Missing optional skills
    for skill in analysis["missing_optional"]:
        if skill in {r["skill"] for r in recommendations}:
            continue
        meta = skills_meta.get(skill, {})
        recommendations.append(
            {
                "skill": skill,
                "reason": (
                    f"Optional but recommended for your target role. "
                    f"({meta.get('description', '')})"
                ),
                "priority": "Medium",
            }
        )

    return recommendations[:max_items]


def get_ai_suggestions(
    student_name: str,
    target_role: str,
    known_skills: list[str],
    missing_skills: list[str],
    readiness_score: float,
    api_key: str | None = None,
) -> str:
    """Return AI-generated career suggestions.

    If *api_key* is provided, this calls the OpenAI Chat Completions API.
    Otherwise it returns a helpful rule-based suggestion string.
    """
    if api_key:
        return _openai_suggestion(
            student_name, target_role, known_skills, missing_skills,
            readiness_score, api_key
        )
    return _rule_based_suggestion(
        student_name, target_role, known_skills, missing_skills, readiness_score
    )


def _rule_based_suggestion(
    student_name: str,
    target_role: str,
    known_skills: list[str],
    missing_skills: list[str],
    readiness_score: float,
) -> str:
    """Produce a motivational and actionable suggestion without an AI API."""
    lines: list[str] = [
        f"Hi **{student_name}**, here is your personalised career guidance:",
        "",
    ]

    if readiness_score >= 80:
        lines.append(
            f"🎉 You are **{readiness_score}% ready** for the **{target_role}** role – great work!"
        )
        lines.append(
            "Consider applying for internships or entry-level positions to gain real-world experience."
        )
    elif readiness_score >= 50:
        lines.append(
            f"📈 You are **{readiness_score}% ready** for the **{target_role}** role – solid progress!"
        )
        lines.append(
            "Focus on the missing required skills listed above to close the gap quickly."
        )
    else:
        lines.append(
            f"🚀 You are **{readiness_score}% ready** for the **{target_role}** role – keep going!"
        )
        lines.append(
            "Build a strong foundation by mastering the beginner-level skills first."
        )

    if missing_skills:
        top3 = ", ".join(f"**{s}**" for s in missing_skills[:3])
        lines += [
            "",
            f"**Top skills to learn next:** {top3}.",
            "Use free resources such as freeCodeCamp, The Odin Project, or official documentation.",
        ]

    if known_skills:
        lines += [
            "",
            f"Your strongest assets right now: {', '.join(f'**{s}**' for s in known_skills[:5])}.",
            "Keep practising projects that demonstrate these skills on GitHub.",
        ]

    lines += [
        "",
        "💡 **Tip:** Build at least one end-to-end project for every new skill you learn.",
        "📝 **Tip:** Update your LinkedIn and GitHub profile as you acquire new skills.",
    ]

    return "\n".join(lines)


def _openai_suggestion(
    student_name: str,
    target_role: str,
    known_skills: list[str],
    missing_skills: list[str],
    readiness_score: float,
    api_key: str,
) -> str:
    """Call OpenAI Chat Completions and return the AI response text."""
    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError:
        return _rule_based_suggestion(
            student_name, target_role, known_skills, missing_skills, readiness_score
        )

    client = OpenAI(api_key=api_key)

    prompt = (
        f"You are a career counsellor for tech students. "
        f"Student name: {student_name}. "
        f"Target role: {target_role}. "
        f"Current skills: {', '.join(known_skills) or 'none'}. "
        f"Missing skills: {', '.join(missing_skills) or 'none'}. "
        f"Readiness score: {readiness_score}%. "
        f"Provide a concise, encouraging, and actionable career advice message "
        f"(max 200 words). Use plain text, no markdown."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:  # noqa: BLE001
        return (
            f"AI suggestion unavailable ({exc}). "
            + _rule_based_suggestion(
                student_name, target_role, known_skills, missing_skills, readiness_score
            )
        )
