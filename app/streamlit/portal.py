"""Entry point of the Dashboard Portal app (viewers only). Same code and tables as the builder app.

Deployed as its own Streamlit app (analytics_accelerator_portal) so that viewer roles can be granted this app
and never see the builder. It runs app.py in portal mode: a catalog of published dashboards and the finished,
read-only dashboard view. All building, publishing and data-source actions are switched off.
"""
import os
import runpy
from pathlib import Path

os.environ["AA_PORTAL"] = "1"
runpy.run_path(str(Path(__file__).parent / "app.py"), run_name="__main__")
