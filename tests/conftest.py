import pytest

from pytest_mock import MockerFixture

from app.carina.db.models import Base as CarinaBase
from app.polaris.db.models import Base as PolarisBase
from app.vela.db.models import Base as VelaBase


@pytest.fixture(autouse=True)
def mock_bases(mocker: MockerFixture) -> None:
    mocker.patch.object(CarinaBase, "prepare")
    mocker.patch.object(PolarisBase, "prepare")
    mocker.patch.object(VelaBase, "prepare")
