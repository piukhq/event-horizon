import json

from typing import TYPE_CHECKING, Type

from flask import Markup

if TYPE_CHECKING:
    from flask_admin.contrib.sqla import ModelView
    from jinja2.runtime import Context
    from sqlalchemy.ext.automap import AutomapBase


def format_json_field(v: Type["ModelView"], c: "Context", model: Type["AutomapBase"], p: str) -> str:
    return (
        Markup("<pre>") + Markup.escape(json.dumps(getattr(model, p), indent=2, ensure_ascii=False)) + Markup("</pre>")
    )
