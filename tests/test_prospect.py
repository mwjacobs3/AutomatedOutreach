"""Tests for the Prospect data model and context building."""

from src.prospect import Prospect


def _make_prospect(**overrides):
    defaults = dict(
        first_name="Sarah",
        last_name="Chen",
        email="sarah@example.com",
        title="VP of Finance",
        company_name="GrowthCo Industries",
    )
    defaults.update(overrides)
    return Prospect(**defaults)


class TestProspectBasics:
    def test_full_name(self):
        p = _make_prospect(first_name="Jane", last_name="Doe")
        assert p.full_name == "Jane Doe"

    def test_defaults_are_none(self):
        p = _make_prospect()
        assert p.linkedin_url is None
        assert p.linkedin_summary is None
        assert p.industry is None
        assert p.pain_points == []

    def test_optional_fields_accepted(self):
        p = _make_prospect(
            linkedin_url="https://linkedin.com/in/sarahchen",
            industry="Manufacturing",
            company_size="200-500 employees",
        )
        assert p.linkedin_url == "https://linkedin.com/in/sarahchen"
        assert p.industry == "Manufacturing"
        assert p.company_size == "200-500 employees"


class TestBuildContextSummary:
    def test_minimal_context(self):
        p = _make_prospect()
        ctx = p.build_context_summary()
        assert "Sarah Chen" in ctx
        assert "VP of Finance" in ctx
        assert "GrowthCo Industries" in ctx

    def test_linkedin_details_included(self):
        p = _make_prospect(
            linkedin_url="https://linkedin.com/in/sarahchen",
            linkedin_summary="Finance leader with 15+ years in scaling operations",
            years_experience="15 years",
            recent_activity="Posted about month-end close challenges",
        )
        ctx = p.build_context_summary()
        assert "LinkedIn Summary" in ctx
        assert "15+ years" in ctx
        assert "Experience: 15 years" in ctx
        assert "month-end close" in ctx

    def test_company_details_included(self):
        p = _make_prospect(
            industry="Manufacturing",
            company_size="200-500 employees",
            company_description="Mid-market manufacturer of industrial equipment",
            tech_stack="QuickBooks Enterprise",
        )
        ctx = p.build_context_summary()
        assert "Industry: Manufacturing" in ctx
        assert "Company Size: 200-500" in ctx
        assert "Company Description" in ctx
        assert "QuickBooks" in ctx

    def test_pain_points_included(self):
        p = _make_prospect(
            pain_points=["Manual consolidation", "No real-time inventory"],
            trigger_event="Series C funding",
        )
        ctx = p.build_context_summary()
        assert "Manual consolidation" in ctx
        assert "No real-time inventory" in ctx
        assert "Trigger Event: Series C funding" in ctx

    def test_empty_optional_fields_excluded(self):
        p = _make_prospect()
        ctx = p.build_context_summary()
        assert "Industry" not in ctx
        assert "LinkedIn Summary" not in ctx
        assert "Pain Points" not in ctx
        assert "Trigger Event" not in ctx
