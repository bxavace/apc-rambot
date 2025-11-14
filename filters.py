"""Jinja filter registrations."""

from markdown import markdown


def register_template_filters(app):
    @app.template_filter("markdown")
    def convert_markdown(text):  # pylint: disable=unused-variable
        return markdown(text, extensions=["extra", "codehilite"])
