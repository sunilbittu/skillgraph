"""SkillGraph AI – Main Streamlit Application.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import os

import streamlit as st

from modules.graph_generator import build_graph, create_plotly_figure
from modules.recommendation import generate_recommendations, get_ai_suggestions
from modules.roadmap import generate_roadmap, roadmap_to_dataframe
from modules.skill_analyzer import (
    analyse_skills,
    list_all_skills,
    list_career_roles,
    load_knowledge_base,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SkillGraph AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load knowledge base once (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def get_kb():
    return load_knowledge_base()


kb = get_kb()
all_skills = list_all_skills(kb)
all_roles = list_career_roles(kb)

# ---------------------------------------------------------------------------
# Sidebar – User Input
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🧠 SkillGraph AI")
    st.markdown("*Intelligent Skill Mapping & Personalised Learning Paths*")
    st.divider()

    student_name = st.text_input("👤 Your Name", value="Student", key="name")

    target_role = st.selectbox(
        "🎯 Target Career Role",
        options=all_roles,
        index=0,
        key="role",
    )

    known_skills_input = st.multiselect(
        "✅ Your Current Skills",
        options=all_skills,
        default=[],
        key="skills",
        help="Select all skills you already know.",
    )

    proficiency = st.select_slider(
        "📊 Overall Proficiency Level",
        options=["Beginner", "Intermediate", "Advanced"],
        value="Beginner",
        key="proficiency",
    )

    domain_interest = st.text_input(
        "💡 Domain / Interest (optional)",
        placeholder="e.g. Web Development, AI, Cloud",
        key="domain",
    )

    st.divider()
    openai_key = st.text_input(
        "🔑 OpenAI API Key (optional)",
        type="password",
        help="Provide your OpenAI key for AI-generated career advice.",
        key="openai_key",
    )

    analyse_btn = st.button("🚀 Analyse My Skills", use_container_width=True)

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("🧠 SkillGraph AI")
st.markdown(
    "**Intelligent Skill Mapping and Personalised Learning Path Recommendation**"
)

if not analyse_btn:
    # Landing / welcome screen
    st.info(
        "👈 Fill in your details in the sidebar and click **Analyse My Skills** to get started."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📊 Skill Gap Analysis")
        st.write(
            "Discover which skills you already have and which ones are standing between "
            "you and your dream role."
        )
    with col2:
        st.markdown("### 🗺️ Visual Skill Graph")
        st.write(
            "See how skills relate to each other through an interactive dependency graph "
            "colour-coded by your status."
        )
    with col3:
        st.markdown("### 🛣️ Learning Roadmap")
        st.write(
            "Get a milestone-based weekly study plan prioritised to get you job-ready as "
            "quickly as possible."
        )
    st.stop()

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
analysis = analyse_skills(known_skills_input, target_role, kb)

# ---------------------------------------------------------------------------
# Header metrics
# ---------------------------------------------------------------------------
st.markdown(f"## 👋 Hello, {student_name}!")
st.markdown(
    f"**Target Role:** {target_role} &nbsp;|&nbsp; "
    f"**Proficiency:** {proficiency} &nbsp;|&nbsp; "
    f"**Domain Interest:** {domain_interest or 'Not specified'}"
)

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("✅ Known Skills", len(analysis["known"]))
col_b.metric("❌ Missing Required", len(analysis["missing_required"]))
col_c.metric("⭐ Missing Optional", len(analysis["missing_optional"]))
col_d.metric("📈 Readiness Score", f"{analysis['readiness_score']}%")

# Readiness progress bar
st.markdown("#### Career Readiness")
st.progress(int(analysis["readiness_score"]))

if analysis["role_description"]:
    st.caption(f"ℹ️ {target_role}: {analysis['role_description']}")

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_graph, tab_gaps, tab_recs, tab_roadmap, tab_ai = st.tabs(
    ["📊 Skill Graph", "🔍 Gap Analysis", "💡 Recommendations", "🗺️ Roadmap", "🤖 AI Advice"]
)

# ── Tab 1: Skill Graph ──────────────────────────────────────────────────────
with tab_graph:
    st.subheader("Interactive Skill Dependency Graph")
    st.markdown(
        "Each node is a skill. Edges show prerequisite relationships "
        "(prerequisite → dependent skill)."
    )

    include_all = st.checkbox("Show all skills in knowledge base", value=False)

    G = build_graph(analysis, kb, include_all=include_all)
    fig = create_plotly_figure(G, title=f"Skill Graph – {target_role}")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Legend:** "
        "🟢 Known &nbsp;|&nbsp; 🔴 Missing Required &nbsp;|&nbsp; "
        "🟠 Missing Optional &nbsp;|&nbsp; 🔵 Unlockable Next"
    )

# ── Tab 2: Gap Analysis ─────────────────────────────────────────────────────
with tab_gaps:
    st.subheader("Skill Gap Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Known Skills")
        if analysis["known"]:
            for s in analysis["known"]:
                meta = kb["skills"].get(s, {})
                st.success(
                    f"**{s}** – {meta.get('description', '')} "
                    f"*(Level: {meta.get('level', '').capitalize()})*"
                )
        else:
            st.info("No known skills selected yet.")

        st.markdown("#### 🔵 Skills You Can Unlock Next")
        if analysis["adjacent"]:
            for s in analysis["adjacent"]:
                meta = kb["skills"].get(s, {})
                st.info(
                    f"**{s}** – {meta.get('description', '')} "
                    f"*(Level: {meta.get('level', '').capitalize()})*"
                )
        else:
            st.write("No immediately unlockable skills found.")

    with col2:
        st.markdown("#### ❌ Missing Required Skills")
        if analysis["missing_required"]:
            for s in analysis["missing_required"]:
                meta = kb["skills"].get(s, {})
                st.error(
                    f"**{s}** – {meta.get('description', '')} "
                    f"*(Level: {meta.get('level', '').capitalize()})*"
                )
        else:
            st.success("You have all required skills for this role! 🎉")

        st.markdown("#### ⭐ Missing Optional Skills")
        if analysis["missing_optional"]:
            for s in analysis["missing_optional"]:
                meta = kb["skills"].get(s, {})
                st.warning(
                    f"**{s}** – {meta.get('description', '')} "
                    f"*(Level: {meta.get('level', '').capitalize()})*"
                )
        else:
            st.success("You have all optional skills for this role! 🎉")

# ── Tab 3: Recommendations ──────────────────────────────────────────────────
with tab_recs:
    st.subheader("Personalised Skill Recommendations")
    st.markdown(
        "Skills are ordered by priority: start from the top for the fastest path "
        "to your goal."
    )

    recommendations = generate_recommendations(analysis, kb)

    if recommendations:
        for i, rec in enumerate(recommendations, start=1):
            priority_icon = "🔴" if rec["priority"] == "High" else "🟡"
            with st.expander(
                f"{priority_icon} **{i}. {rec['skill']}** – Priority: {rec['priority']}"
            ):
                st.write(rec["reason"])
                meta = kb["skills"].get(rec["skill"], {})
                st.caption(
                    f"Category: {meta.get('category', 'N/A')} | "
                    f"Level: {meta.get('level', 'N/A').capitalize()}"
                )
    else:
        st.success(
            "You already have all the recommended skills for this role. "
            "Consider exploring advanced topics or a more senior role."
        )

# ── Tab 4: Roadmap ──────────────────────────────────────────────────────────
with tab_roadmap:
    st.subheader("Milestone-Based Learning Roadmap")
    st.markdown(
        "Each phase groups skills into a realistic study block. "
        f"Assumes ~10 study hours per week."
    )

    recommendations = generate_recommendations(analysis, kb, max_items=20)
    phases = generate_roadmap(recommendations, kb)

    if phases:
        for phase in phases:
            priority_colour = "🔴" if phase["priority"] == "High" else "🟡"
            st.markdown(f"### {priority_colour} {phase['label']}")
            cols = st.columns(min(len(phase["skills"]), 4))
            for idx, skill in enumerate(phase["skills"]):
                meta = kb["skills"].get(skill, {})
                with cols[idx % len(cols)]:
                    st.markdown(
                        f"**{skill}**  \n"
                        f"*{meta.get('category', '')}*  \n"
                        f"Level: {meta.get('level', '').capitalize()}"
                    )

        st.divider()
        st.subheader("📋 Roadmap Table")
        df = roadmap_to_dataframe(phases)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.success(
            "No additional learning required for this role based on your current skills!"
        )

# ── Tab 5: AI Advice ────────────────────────────────────────────────────────
with tab_ai:
    st.subheader("🤖 AI-Assisted Career Advice")

    api_key = openai_key or os.environ.get("OPENAI_API_KEY", "")

    with st.spinner("Generating personalised advice…"):
        advice = get_ai_suggestions(
            student_name=student_name,
            target_role=target_role,
            known_skills=analysis["known"],
            missing_skills=analysis["missing_required"],
            readiness_score=analysis["readiness_score"],
            api_key=api_key or None,
        )

    st.markdown(advice)

    if not api_key:
        st.caption(
            "💡 Provide an OpenAI API key in the sidebar to receive AI-powered personalised advice."
        )
