"""Tests for SkillGraph AI modules."""
from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest

# Ensure the project root is on sys.path so imports work without installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.skill_analyzer import (
    analyse_skills,
    list_all_skills,
    list_career_roles,
    load_knowledge_base,
    normalise_skill,
)
from modules.graph_generator import build_graph, create_plotly_figure
from modules.recommendation import generate_recommendations, get_ai_suggestions
from modules.roadmap import generate_roadmap, roadmap_to_dataframe


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def kb():
    return load_knowledge_base()


@pytest.fixture(scope="module")
def full_stack_analysis(kb):
    known = ["HTML", "CSS", "JavaScript"]
    return analyse_skills(known, "Full Stack Developer", kb)


# ---------------------------------------------------------------------------
# skill_analyzer tests
# ---------------------------------------------------------------------------

class TestLoadKnowledgeBase:
    def test_loads_skills(self, kb):
        assert "skills" in kb
        assert len(kb["skills"]) > 0

    def test_loads_career_paths(self, kb):
        assert "career_paths" in kb
        assert len(kb["career_paths"]) > 0

    def test_loads_dependencies(self, kb):
        assert "dependencies" in kb

    def test_custom_path(self):
        data = {
            "skills": {"Python": {"description": "test", "category": "Programming", "level": "beginner"}},
            "dependencies": {},
            "career_paths": {},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            tmp_path = f.name
        try:
            loaded = load_knowledge_base(tmp_path)
            assert "Python" in loaded["skills"]
        finally:
            os.unlink(tmp_path)


class TestNormaliseSkill:
    def test_exact_match(self, kb):
        skills = list_all_skills(kb)
        assert normalise_skill("Python", skills) == "Python"

    def test_case_insensitive(self, kb):
        skills = list_all_skills(kb)
        assert normalise_skill("python", skills) == "Python"
        assert normalise_skill("REACT", skills) == "React"

    def test_missing_skill_returns_none(self, kb):
        skills = list_all_skills(kb)
        assert normalise_skill("NonExistentSkill123", skills) is None


class TestAnalyseSkills:
    def test_basic_structure(self, full_stack_analysis):
        keys = {"known", "required", "optional", "missing_required",
                "missing_optional", "readiness_score", "role_description", "adjacent"}
        assert keys.issubset(full_stack_analysis.keys())

    def test_known_skills_validated(self, full_stack_analysis):
        assert "HTML" in full_stack_analysis["known"]
        assert "CSS" in full_stack_analysis["known"]
        assert "JavaScript" in full_stack_analysis["known"]

    def test_readiness_score_range(self, full_stack_analysis):
        score = full_stack_analysis["readiness_score"]
        assert 0.0 <= score <= 100.0

    def test_missing_required_not_in_known(self, full_stack_analysis):
        known_set = set(full_stack_analysis["known"])
        for s in full_stack_analysis["missing_required"]:
            assert s not in known_set

    def test_perfect_score_when_all_known(self, kb):
        role = "Frontend Developer"
        required = kb["career_paths"][role]["required_skills"]
        analysis = analyse_skills(required, role, kb)
        assert analysis["readiness_score"] == 100.0
        assert analysis["missing_required"] == []

    def test_zero_score_when_nothing_known(self, kb):
        analysis = analyse_skills([], "Frontend Developer", kb)
        assert analysis["readiness_score"] == 0.0

    def test_case_insensitive_input(self, kb):
        analysis = analyse_skills(["python", "flask"], "Backend Developer", kb)
        assert "Python" in analysis["known"]
        assert "Flask" in analysis["known"]

    def test_unknown_role_returns_empty(self, kb):
        analysis = analyse_skills(["Python"], "Unknown Role XYZ", kb)
        assert analysis["required"] == []
        assert analysis["readiness_score"] == 0.0

    def test_adjacent_skills_all_prereqs_met(self, kb):
        # HTML + CSS + JavaScript should unlock React (prereqs: JS, HTML, CSS)
        analysis = analyse_skills(["HTML", "CSS", "JavaScript"], "Full Stack Developer", kb)
        assert "React" in analysis["adjacent"]

    def test_list_career_roles(self, kb):
        roles = list_career_roles(kb)
        assert isinstance(roles, list)
        assert "Full Stack Developer" in roles

    def test_list_all_skills(self, kb):
        skills = list_all_skills(kb)
        assert isinstance(skills, list)
        assert "Python" in skills


# ---------------------------------------------------------------------------
# graph_generator tests
# ---------------------------------------------------------------------------

class TestBuildGraph:
    def test_known_nodes_present(self, full_stack_analysis, kb):
        G = build_graph(full_stack_analysis, kb)
        for s in full_stack_analysis["known"]:
            assert G.has_node(s)

    def test_missing_nodes_present(self, full_stack_analysis, kb):
        G = build_graph(full_stack_analysis, kb)
        for s in full_stack_analysis["missing_required"]:
            assert G.has_node(s)

    def test_node_status_attribute(self, full_stack_analysis, kb):
        G = build_graph(full_stack_analysis, kb)
        for node, data in G.nodes(data=True):
            assert "status" in data

    def test_known_node_has_correct_status(self, full_stack_analysis, kb):
        G = build_graph(full_stack_analysis, kb)
        for s in full_stack_analysis["known"]:
            assert G.nodes[s]["status"] == "known"

    def test_missing_required_status(self, full_stack_analysis, kb):
        G = build_graph(full_stack_analysis, kb)
        for s in full_stack_analysis["missing_required"]:
            if G.has_node(s):
                assert G.nodes[s]["status"] == "missing_required"

    def test_include_all_flag(self, full_stack_analysis, kb):
        G_partial = build_graph(full_stack_analysis, kb, include_all=False)
        G_all = build_graph(full_stack_analysis, kb, include_all=True)
        assert len(G_all) >= len(G_partial)

    def test_edges_are_valid(self, full_stack_analysis, kb):
        G = build_graph(full_stack_analysis, kb)
        for u, v in G.edges():
            assert G.has_node(u)
            assert G.has_node(v)

    def test_empty_analysis_returns_empty_graph(self, kb):
        empty = {
            "known": [],
            "missing_required": [],
            "missing_optional": [],
            "adjacent": [],
        }
        G = build_graph(empty, kb, include_all=False)
        assert len(G) == 0


class TestCreatePlotlyFigure:
    def test_returns_figure(self, full_stack_analysis, kb):
        import plotly.graph_objects as go
        G = build_graph(full_stack_analysis, kb)
        fig = create_plotly_figure(G)
        assert isinstance(fig, go.Figure)

    def test_empty_graph_returns_figure(self, kb):
        import plotly.graph_objects as go
        import networkx as nx
        G = nx.DiGraph()
        fig = create_plotly_figure(G)
        assert isinstance(fig, go.Figure)

    def test_custom_title(self, full_stack_analysis, kb):
        G = build_graph(full_stack_analysis, kb)
        fig = create_plotly_figure(G, title="My Custom Title")
        assert fig.layout.title.text == "My Custom Title"


# ---------------------------------------------------------------------------
# recommendation tests
# ---------------------------------------------------------------------------

class TestGenerateRecommendations:
    def test_returns_list(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        assert isinstance(recs, list)

    def test_respects_max_items(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb, max_items=3)
        assert len(recs) <= 3

    def test_recommended_skills_not_in_known(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        known_set = set(full_stack_analysis["known"])
        for rec in recs:
            assert rec["skill"] not in known_set

    def test_rec_has_required_keys(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        for rec in recs:
            assert "skill" in rec
            assert "reason" in rec
            assert "priority" in rec

    def test_priority_values_valid(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        valid = {"High", "Medium", "Low"}
        for rec in recs:
            assert rec["priority"] in valid

    def test_no_role_skills_recommended_when_all_known(self, kb):
        role = "Frontend Developer"
        required = kb["career_paths"][role]["required_skills"]
        optional = kb["career_paths"][role]["optional_skills"]
        all_known = list(set(required + optional))
        analysis = analyse_skills(all_known, role, kb)
        recs = generate_recommendations(analysis, kb)
        # None of the role-specific required/optional skills should appear
        role_skills = set(required + optional)
        for rec in recs:
            assert rec["skill"] not in role_skills


class TestGetAiSuggestions:
    def test_rule_based_no_api_key(self):
        result = get_ai_suggestions(
            student_name="Alice",
            target_role="Backend Developer",
            known_skills=["Python"],
            missing_skills=["Flask", "Docker"],
            readiness_score=30.0,
            api_key=None,
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Alice" in result

    def test_rule_based_high_readiness(self):
        result = get_ai_suggestions(
            student_name="Bob",
            target_role="Frontend Developer",
            known_skills=["HTML", "CSS", "JavaScript", "React", "Git", "REST APIs"],
            missing_skills=[],
            readiness_score=100.0,
            api_key=None,
        )
        assert "Bob" in result
        assert "100" in result

    def test_rule_based_mid_readiness(self):
        result = get_ai_suggestions(
            student_name="Carol",
            target_role="Data Scientist",
            known_skills=["Python", "NumPy"],
            missing_skills=["Pandas", "Machine Learning"],
            readiness_score=60.0,
            api_key=None,
        )
        assert "Carol" in result


# ---------------------------------------------------------------------------
# roadmap tests
# ---------------------------------------------------------------------------

class TestGenerateRoadmap:
    def test_returns_list(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        phases = generate_roadmap(recs, kb)
        assert isinstance(phases, list)

    def test_phases_have_required_keys(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        phases = generate_roadmap(recs, kb)
        for phase in phases:
            assert "phase" in phase
            assert "label" in phase
            assert "skills" in phase
            assert "start_week" in phase
            assert "end_week" in phase
            assert "priority" in phase

    def test_phase_numbers_sequential(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        phases = generate_roadmap(recs, kb)
        for i, phase in enumerate(phases, start=1):
            assert phase["phase"] == i

    def test_end_week_gte_start_week(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb)
        phases = generate_roadmap(recs, kb)
        for phase in phases:
            assert phase["end_week"] >= phase["start_week"]

    def test_all_recommended_skills_in_roadmap(self, full_stack_analysis, kb):
        recs = generate_recommendations(full_stack_analysis, kb, max_items=20)
        phases = generate_roadmap(recs, kb)
        roadmap_skills = {s for p in phases for s in p["skills"]}
        rec_skills = {r["skill"] for r in recs}
        assert rec_skills == roadmap_skills

    def test_empty_recommendations_returns_empty(self, kb):
        phases = generate_roadmap([], kb)
        assert phases == []

    def test_roadmap_to_dataframe(self, full_stack_analysis, kb):
        import pandas as pd
        recs = generate_recommendations(full_stack_analysis, kb)
        phases = generate_roadmap(recs, kb)
        df = roadmap_to_dataframe(phases)
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"Phase", "Skill", "Weeks", "Priority"}
        rec_skills = {r["skill"] for r in recs}
        assert set(df["Skill"].tolist()) == rec_skills
