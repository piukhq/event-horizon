import base64
import pickle

from abc import ABC
from typing import Type, TypeVar

TSessionDataMethodsMixin = TypeVar(  # pylint: disable=invalid-name
    "TSessionDataMethodsMixin", bound="SessionDataMethodsMixin"
)


class SessionDataMethodsMixin(ABC):
    def to_base64_str(self) -> str:
        return base64.b64encode(pickle.dumps(self)).decode()

    @classmethod
    def from_base64_str(cls: Type[TSessionDataMethodsMixin], base64_session_data: str) -> TSessionDataMethodsMixin:
        try:
            parsed_data = pickle.loads(base64.b64decode(base64_session_data.encode()))
        except Exception as ex:
            raise ValueError("unexpected value for 'base64_session_data'") from ex

        if not isinstance(parsed_data, cls):
            raise TypeError(f"'base64_session_data' is not a valid {cls.__name__}")

        return parsed_data
