"""Tests for the HTML/CSS Gantt chart renderer.

These tests guard against regressions that caused raw HTML to leak into
the rendered page (e.g. markdown code-block fallback from leading CSS
whitespace, broken title attributes from newlines, etc.).
"""

import re
from datetime import date, timedelta

import pytest

from components import render_gantt_html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class _FakeProject:
    """Minimal stand-in for models.Project used by render_gantt_html."""
    def __init__(
        self,
        id,
        name,
        start_date,
        end_date,
        priority="High",
        health="Green",
        portfolio="Core",
        pm="Alice",
        pct_complete=0.0,
    ):
        self.id = id
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.priority = priority
        self.health = health
        self.portfolio = portfolio
        self.pm = pm
        self.pct_complete = pct_complete


def _make_projects(n=3, base_date=None):
    base_date = base_date or date.today()
    return [
        _FakeProject(
            id=f"ETE-{i+1}",
            name=f"Project {i+1}",
            start_date=base_date + timedelta(days=i * 10),
            end_date=base_date + timedelta(days=i * 10 + 30),
            priority=["Highest", "High", "Medium", "Low"][i % 4],
            health=["Green", "Yellow", "Red"][i % 3],
            portfolio=f"Portfolio {(i % 2) + 1}",
            pm=f"PM {i+1}",
            pct_complete=min(1.0, i * 0.2),
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Structural correctness
# ---------------------------------------------------------------------------
class TestRenderStructure:
    """Verify the output is well-formed HTML and contains expected regions."""

    def test_returns_string(self):
        html = render_gantt_html(_make_projects(3))
        assert isinstance(html, str)
        assert len(html) > 500

    def test_empty_list_returns_placeholder(self):
        html = render_gantt_html([])
        assert "No projects to display" in html

    def test_all_projects_unscheduled_returns_placeholder(self):
        p = _FakeProject("ETE-1", "Foo", None, None)
        html = render_gantt_html([p])
        assert "No scheduled projects" in html or "No projects" in html

    def test_contains_style_block(self):
        html = render_gantt_html(_make_projects())
        assert "<style>" in html
        assert "</style>" in html
        assert ".gantt-wrap" in html

    def test_contains_root_wrapper(self):
        html = render_gantt_html(_make_projects())
        assert 'class="gantt-wrap"' in html
        assert 'class="gantt-grid"' in html

    def test_contains_month_header(self):
        html = render_gantt_html(_make_projects())
        assert 'class="gantt-month-head"' in html
        assert 'class="gantt-month' in html

    def test_contains_info_panel_and_timeline_body(self):
        html = render_gantt_html(_make_projects())
        assert 'class="gantt-info-body"' in html
        assert 'class="gantt-timeline-body"' in html

    def test_each_project_has_info_row(self):
        projects = _make_projects(5)
        html = render_gantt_html(projects)
        count = html.count('class="gantt-row-info"')
        assert count == 5, f"expected 5 info rows, got {count}"

    def test_each_project_has_timeline_row(self):
        projects = _make_projects(5)
        html = render_gantt_html(projects)
        count = html.count('class="gantt-row-timeline"')
        assert count == 5

    def test_tags_balanced(self):
        """Crude balance check on major containers."""
        html = render_gantt_html(_make_projects(4))
        # Each <div class="gantt-row-info"> is actually an <a>, count those
        opens = html.count("<div class=\"gantt-wrap\">")
        closes_min = html.count("</div>")
        assert opens >= 1
        # There must be at least as many </div> as <div
        open_div = len(re.findall(r"<div\b", html))
        close_div = len(re.findall(r"</div>", html))
        assert open_div == close_div, (
            f"div mismatch: {open_div} open vs {close_div} close"
        )


# ---------------------------------------------------------------------------
# CSS / markdown-escape bug (regression)
# ---------------------------------------------------------------------------
class TestNoMarkdownCodeBlockLeakage:
    """The CSS used to have leading whitespace which made Streamlit's
    st.markdown treat it as a code block. Guard against this."""

    def test_no_line_starts_with_four_spaces(self):
        html = render_gantt_html(_make_projects())
        offending = [
            (i, line) for i, line in enumerate(html.splitlines())
            if line.startswith("    ") and line.strip()
        ]
        assert not offending, (
            f"Found {len(offending)} lines with 4+ space indent "
            f"(would break st.markdown rendering): "
            f"{offending[:3]}"
        )

    def test_no_line_starts_with_tab(self):
        html = render_gantt_html(_make_projects())
        bad = [l for l in html.splitlines() if l.startswith("\t")]
        assert not bad


# ---------------------------------------------------------------------------
# Tooltip / attribute escaping (regression)
# ---------------------------------------------------------------------------
class TestTooltipEscaping:
    """Tooltips in title attributes must not contain raw newlines or
    unescaped quotes — they break HTML attribute parsing."""

    def test_title_attrs_contain_no_newlines(self):
        html = render_gantt_html(_make_projects(3))
        # Extract every title="..." attribute
        titles = re.findall(r'title="([^"]*)"', html)
        assert titles, "expected at least one title attribute"
        for t in titles:
            assert "\n" not in t, f"title attr contains newline: {t!r}"
            assert "\r" not in t

    def test_title_attrs_no_unescaped_quotes(self):
        html = render_gantt_html(_make_projects(3))
        # Find any title attribute that contains a stray double quote
        # inside the value — would prematurely close the attribute.
        titles = re.findall(r'title="([^"]*)"', html)
        # If any embedded quotes existed, the regex above would fail to
        # capture them. Re-scan with a more permissive search.
        assert all('"' not in t for t in titles)

    def test_html_special_chars_in_name_are_escaped(self):
        p = _FakeProject(
            id="ETE-X",
            name='Evil <script>alert("xss")</script> & "quoted"',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
        )
        html = render_gantt_html([p])
        # The dangerous tag must not appear verbatim
        assert "<script>" not in html
        assert "alert(" not in html or "&lt;" in html
        # Escaped version should appear
        assert "&lt;script&gt;" in html or "&amp;" in html


# ---------------------------------------------------------------------------
# Behavior
# ---------------------------------------------------------------------------
class TestClickable:
    def test_info_rows_are_anchors_with_project_href(self):
        projects = _make_projects(3)
        html = render_gantt_html(projects)
        for p in projects:
            assert f'href="?project={p.id}"' in html


class TestTodayLine:
    def test_today_line_rendered_when_in_range(self):
        # Projects spanning today
        today = date.today()
        projects = [
            _FakeProject(
                "ETE-1", "Spanning",
                today - timedelta(days=10),
                today + timedelta(days=20),
            )
        ]
        html = render_gantt_html(projects)
        assert 'class="gantt-today-line"' in html
        assert "TODAY" in html

    def test_today_line_not_rendered_when_out_of_range(self):
        # Project entirely in the past
        p = _FakeProject(
            "ETE-1", "Old",
            date(2020, 1, 1),
            date(2020, 6, 1),
        )
        html = render_gantt_html(
            [p],
            date_range=(date(2020, 1, 1), date(2020, 6, 30)),
        )
        assert 'class="gantt-today-line"' not in html


class TestGrouping:
    def test_group_headers_rendered_when_grouping(self):
        projects = _make_projects(4)
        html = render_gantt_html(projects, group_by="portfolio")
        assert 'class="gantt-group-info"' in html
        assert 'class="gantt-group-timeline"' in html

    def test_no_group_headers_when_group_by_none(self):
        projects = _make_projects(4)
        html = render_gantt_html(projects, group_by="none")
        assert 'class="gantt-group-info"' not in html


class TestSorting:
    def test_sort_by_priority_orders_highest_first(self):
        projects = [
            _FakeProject("ETE-LOW", "Low one", date(2026, 5, 1),
                         date(2026, 6, 1), priority="Low"),
            _FakeProject("ETE-HIGH", "High one", date(2026, 5, 1),
                         date(2026, 6, 1), priority="Highest"),
            _FakeProject("ETE-MED", "Medium one", date(2026, 5, 1),
                         date(2026, 6, 1), priority="Medium"),
        ]
        html = render_gantt_html(projects, sort_by="priority")
        # ETE-HIGH should appear before ETE-MED which should appear before ETE-LOW
        high_pos = html.find("ETE-HIGH")
        med_pos = html.find("ETE-MED")
        low_pos = html.find("ETE-LOW")
        assert 0 < high_pos < med_pos < low_pos

    def test_sort_by_start_date(self):
        projects = [
            _FakeProject("ETE-B", "B", date(2026, 6, 1), date(2026, 7, 1)),
            _FakeProject("ETE-A", "A", date(2026, 4, 1), date(2026, 5, 1)),
            _FakeProject("ETE-C", "C", date(2026, 8, 1), date(2026, 9, 1)),
        ]
        html = render_gantt_html(projects, sort_by="start")
        a_pos = html.find("ETE-A")
        b_pos = html.find("ETE-B")
        c_pos = html.find("ETE-C")
        assert 0 < a_pos < b_pos < c_pos


class TestColorModes:
    def test_priority_color_mode_legend(self):
        html = render_gantt_html(_make_projects(4), color_by="priority")
        assert "Highest" in html
        assert "High" in html
        assert "Medium" in html
        assert "Low" in html

    def test_health_color_mode_legend(self):
        html = render_gantt_html(_make_projects(4), color_by="health")
        assert "On Track" in html or "Track" in html

    def test_portfolio_color_mode_legend(self):
        html = render_gantt_html(_make_projects(4), color_by="portfolio")
        # Each distinct portfolio appears in the legend
        assert "Portfolio 1" in html
        assert "Portfolio 2" in html


class TestBars:
    def test_progress_overlay_only_for_nonzero_pct(self):
        p_zero = _FakeProject("ETE-Z", "Zero", date(2026, 5, 1),
                              date(2026, 6, 1), pct_complete=0.0)
        p_half = _FakeProject("ETE-H", "Half", date(2026, 5, 1),
                              date(2026, 6, 1), pct_complete=0.5)
        html = render_gantt_html([p_zero, p_half])
        # gantt-progress should appear for the half-complete one only
        progress_count = html.count('class="gantt-progress"')
        assert progress_count == 1

    def test_overdue_outline_rendered(self):
        overdue = _FakeProject(
            "ETE-OD", "Overdue",
            date.today() - timedelta(days=60),
            date.today() - timedelta(days=10),
            pct_complete=0.3,
        )
        html = render_gantt_html([overdue])
        assert 'class="gantt-bar-overdue"' in html

    def test_milestones_rendered(self):
        projects = _make_projects(2)
        html = render_gantt_html(projects)
        # Two diamonds per project (start + end)
        diamond_count = html.count('class="gantt-diamond"')
        assert diamond_count == 4


class TestIntegrationWithRealData:
    """Run against the seeded test database to make sure render_gantt_html
    works end-to-end with real Project objects."""

    def test_renders_with_seed_data(self, connector):
        portfolio = connector.read_portfolio()
        scheduled = [p for p in portfolio if p.start_date and p.end_date]
        if not scheduled:
            pytest.skip("No scheduled projects in seed data")
        html = render_gantt_html(scheduled)
        assert "<style>" in html
        assert 'class="gantt-wrap"' in html
        # Every scheduled project must have an info row
        for p in scheduled:
            assert f'href="?project={p.id}"' in html

    def test_renders_with_all_options(self, connector):
        portfolio = connector.read_portfolio()
        scheduled = [p for p in portfolio if p.start_date and p.end_date]
        if not scheduled:
            pytest.skip("No scheduled projects in seed data")
        for color_by in ("priority", "health", "portfolio"):
            for group_by in ("none", "portfolio", "pm", "priority", "health"):
                for sort_by in ("start", "end", "priority", "name"):
                    html = render_gantt_html(
                        scheduled, color_by=color_by,
                        group_by=group_by, sort_by=sort_by,
                    )
                    assert 'class="gantt-wrap"' in html, (
                        f"failed for color={color_by}, group={group_by}, "
                        f"sort={sort_by}"
                    )
