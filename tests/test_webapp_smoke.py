"""Gate 7 B1 — Streamlit dashboard smoke test.

Streamlit is stubbed (so it need not be installed) and every page is driven via
main() to confirm the dashboard loads and renders without crashing, including the
new project-loading path. Chart pages need Plotly, so the test skips when Plotly
is absent (it runs in CI where Plotly is installed).
"""

import sys

import pytest

PAGES = [
    "Overview", "Mass & energy", "Low-fidelity simulation", "Dynamics screening",
    "Branch trade-off", "Packaging", "Supplier evidence", "RFI builder",
    "Forbidden claim checker",
]


class _Sidebar:
    def __init__(self):
        self.page = "Overview"

    def radio(self, label, options, *a, **k):
        return self.page

    def text_input(self, label, *a, **k):
        return ""

    def caption(self, *a, **k):
        return None


class _FakeSt:
    def __init__(self):
        self.sidebar = _Sidebar()

    def selectbox(self, label, options, *a, **k):
        return list(options)[0]

    def slider(self, label, *a, **k):
        return a[2] if len(a) >= 3 else k.get("value", 0)

    def button(self, *a, **k):
        return False

    def text_area(self, *a, **k):
        return k.get("value", "")

    def __getattr__(self, name):  # set_page_config/title/header/dataframe/plotly_chart/...
        def _noop(*a, **k):
            return None

        return _noop


@pytest.fixture
def app_with_fake_st():
    pytest.importorskip("plotly")  # chart pages need plotly
    fake = _FakeSt()
    saved_st = sys.modules.get("streamlit")
    saved_app = sys.modules.pop("haen.webapp.app", None)
    sys.modules["streamlit"] = fake
    try:
        import haen.webapp.app as app
        yield app, fake
    finally:
        sys.modules.pop("haen.webapp.app", None)
        if saved_st is not None:
            sys.modules["streamlit"] = saved_st
        else:
            sys.modules.pop("streamlit", None)
        if saved_app is not None:
            sys.modules["haen.webapp.app"] = saved_app


@pytest.mark.parametrize("page", PAGES)
def test_each_page_renders(app_with_fake_st, page):
    app, fake = app_with_fake_st
    fake.sidebar.page = page
    app.main()  # must not raise


def test_main_default_overview(app_with_fake_st):
    app, fake = app_with_fake_st
    fake.sidebar.page = "Overview"
    app.main()
