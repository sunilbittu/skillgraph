# SkillGraph AI

**Intelligent Skill Mapping and Personalised Learning Path Recommendation**

SkillGraph AI is a Python-based intelligent system that helps students understand their existing skills, identify missing competencies, and receive a personalised roadmap toward their desired career path. The system builds an interactive visual skill graph, performs gap analysis, and uses AI to recommend what to learn next in a structured sequence.

---

## Features

| Module | Description |
|---|---|
| **User Input** | Collects name, known skills, proficiency level, interests, and target role |
| **Skill Analysis** | Maps skill dependencies (e.g. HTML/CSS → JavaScript → React) |
| **Graph Generator** | Interactive NetworkX + Plotly skill dependency graph |
| **Recommendation Engine** | Rule-based (+ optional OpenAI) suggestions ordered by priority |
| **Roadmap Module** | Milestone-based weekly learning plan |
| **Dashboard** | Streamlit dashboard with gap analysis, graph, recommendations, and AI advice |

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io) |
| Backend | Python 3.9+ |
| Knowledge Base | JSON |
| AI | OpenAI API (optional; rule-based fallback included) |
| Visualisation | NetworkX, Plotly |
| Data Processing | Pandas |

---

## Project Structure

```
skillgraph/
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies
├── data/
│   └── skill_graph.json     # Skill knowledge base (skills, dependencies, career paths)
├── modules/
│   ├── __init__.py
│   ├── skill_analyzer.py    # Gap analysis and skill normalisation
│   ├── graph_generator.py   # NetworkX graph + Plotly visualisation
│   ├── recommendation.py    # Rule-based and AI recommendation engine
│   └── roadmap.py           # Milestone-based learning roadmap generator
└── tests/
    └── test_modules.py      # pytest test suite (45 tests)
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/sunilbittu/skillgraph.git
cd skillgraph
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

### 4. (Optional) Enable AI advice

Set your OpenAI API key either as an environment variable:

```bash
export OPENAI_API_KEY=sk-...
streamlit run app.py
```

…or paste it directly into the sidebar of the running app.

---

## Running Tests

```bash
pip install pytest
pytest tests/test_modules.py -v
```

All 45 tests should pass.

---

## How It Works

1. **Input** – Enter your name, select your current skills from the dropdown, choose your target career role, and (optionally) your proficiency level and domain interest.
2. **Analysis** – The system validates your skills against the knowledge base, identifies required/optional missing skills, and calculates a readiness score (0–100 %).
3. **Graph** – An interactive Plotly graph shows skill nodes colour-coded by status:
   - 🟢 **Green** = Known
   - 🔴 **Red** = Missing (Required)
   - 🟠 **Orange** = Missing (Optional)
   - 🔵 **Blue** = Immediately unlockable (all prerequisites met)
4. **Recommendations** – Skills are ranked by priority; adjacent (unlockable) skills appear first, followed by required then optional gaps.
5. **Roadmap** – Skills are grouped into timed learning phases (assumes ~10 study hours/week).
6. **AI Advice** – Personalised encouragement and actionable tips (rule-based by default; GPT-3.5 when an API key is provided).

---

## Supported Career Roles

- Full Stack Developer
- Frontend Developer
- Backend Developer
- Data Scientist
- ML Engineer
- DevOps Engineer
- Cloud Engineer
- Java Developer
- Cybersecurity Analyst

---

## Extending the Knowledge Base

Edit `data/skill_graph.json` to add new skills, dependencies, or career paths:

```json
{
  "skills": {
    "MySkill": { "description": "...", "category": "...", "level": "beginner|intermediate|advanced" }
  },
  "dependencies": {
    "MySkill": ["Prerequisite1", "Prerequisite2"]
  },
  "career_paths": {
    "My Role": {
      "required_skills": ["MySkill"],
      "optional_skills": [],
      "description": "..."
    }
  }
}
```

---

## Future Enhancements

- Resume analyser integration
- Job description matching
- GitHub profile analysis
- Placement-readiness scoring
- Campus analytics dashboard
