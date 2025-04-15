from src.mission_type import Mission, GeoSpecificSpeedLimit
from src.config import *
from src.wpl_parser import WPLParser
from src.signature import MissionSignature
import pytest


@pytest.fixture
def mission() -> Mission:
    """
    Создание миссии

    Return:
        Mission: объект миссии
    """
    parser = WPLParser("module2.wpl")
    points = parser.parse()
    speed_limits = [GeoSpecificSpeedLimit(0, 30)]
    home = points[0]

    mission = Mission(home, points, speed_limits, armed=True)

    return mission


def test_mission_signature_false(mission):
    """
    Проверка работы при компрометации миссии

    Args:
        mission (Mission): объект получаемый из инъекции
    """

    mission_with_signature = MissionSignature.register_mission_signature(
        mission, secret_key="secret_key"
    )

    mission_with_signature.speed_limits = [GeoSpecificSpeedLimit(3, 60)]

    # Проверяем вовзращается ли False
    assert not MissionSignature.verify_mission(
        mission_with_signature, secret_key="secret_key"
    )


def test_mission_signature_true(mission):
    """
    Проверка работы при правильном поведении

    Args:
        mission (Mission): объект получаемый из инъекции
    """
    mission_with_signature = MissionSignature.register_mission_signature(
        mission, secret_key="secret_key"
    )

    # Проверяем вовзращается ли True
    assert MissionSignature.verify_mission(
        mission_with_signature, secret_key="secret_key"
    )
