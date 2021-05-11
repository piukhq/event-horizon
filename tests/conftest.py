from typing import Generator
from unittest import mock

import pytest


@pytest.fixture(scope="session")
def mock_sqlalchemy_automap() -> Generator:
    with mock.patch("sqlalchemy.ext.automap.automap_base", autospec=True):
        yield


@pytest.fixture(scope="session", autouse=True)
def mock_polaris_metadata(mock_sqlalchemy_automap: None) -> Generator:
    with mock.patch("app.polaris.db.models.metadata", autospec=True) as mock_metadata:
        yield mock_metadata


@pytest.fixture(scope="session", autouse=True)
def mock_vela_metadata(mock_sqlalchemy_automap: None) -> Generator:
    with mock.patch("app.vela.db.models.metadata", autospec=True) as mock_metadata:
        yield mock_metadata
