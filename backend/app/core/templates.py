from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

email_templates = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR / "email"),
    autoescape=select_autoescape(["html"]),
)
