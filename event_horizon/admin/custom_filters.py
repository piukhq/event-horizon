from typing import Any

from flask_admin.babel import lazy_gettext
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from sqlalchemy.orm.query import Query


class StringInList(BaseSQLAFilter):
    def apply(self, query: Query, value: str, _: Any = None) -> None:
        return query.filter(self.column.contains(f"{{{value}}}"))

    def operation(self) -> None:
        return lazy_gettext("in list")


class StringNotInList(BaseSQLAFilter):
    def apply(self, query: Query, value: str, _: Any = None) -> None:
        return query.filter(~self.column.contains(f"{{{value}}}"))

    def operation(self) -> None:
        return lazy_gettext("not in list")
