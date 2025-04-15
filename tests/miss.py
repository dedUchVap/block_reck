"""Тесты для проверки компрометации миссии"""

import pytest
from multiprocessing import Queue
from geopy import Point as GeoPoint
from src.mission_type import Mission
from src.event_types import Event
from src.queues_dir import QueuesDirectory
from src.safety_block import BaseSafetyBlock
from src.control_system import BaseControlSystem
from src.security_monitory import BaseSecurityMonitor
from src.config import SECRET_KEY

class TestSafetyBlock(BaseSafetyBlock):
    """Тестовая реализация SafetyBlock для проверки компрометации"""
    def _set_new_direction(self, direction: float):
        self._direction = direction

    def _set_new_speed(self, speed: float):
        self._speed = speed

    def _lock_cargo(self, _):
        pass

    def _release_cargo(self, _):
        pass

    def _send_speed_to_consumers(self):
        pass

    def _send_direction_to_consumers(self):
        pass

    def _send_lock_cargo_to_consumers(self):
        pass

    def _send_release_cargo_to_consumers(self):
        pass

class TestControlSystem(BaseControlSystem):
    """Тестовая реализация ControlSystem для проверки компрометации"""
    def _send_speed_and_direction_to_consumers(self, speed: float, direction: float):
        self._speed = speed
        self._direction_grad = direction

    def _release_cargo(self):
        pass

    def _lock_cargo(self):
        pass

class TestSecurityMonitor(BaseSecurityMonitor):
    """Тестовая реализация SecurityMonitor для проверки компрометации"""
    def _check_event(self, event: Event):
        return True

@pytest.fixture
def queues_dir():
    """Создание каталога очередей для тестов"""
    return QueuesDirectory()

@pytest.fixture
def safety_block(queues_dir):
    """Создание тестового блока безопасности"""
    return TestSafetyBlock(queues_dir)

@pytest.fixture
def control_system(queues_dir):
    """Создание тестовой системы управления"""
    return TestControlSystem(queues_dir)

@pytest.fixture
def security_monitor(queues_dir):
    """Создание тестового монитора безопасности"""
    return TestSecurityMonitor(queues_dir)

@pytest.fixture
def valid_mission():
    """Создание валидной миссии"""
    return Mission(
        waypoints=[GeoPoint(55.0, 37.0), GeoPoint(55.1, 37.1)],
        speed_limits=[50, 50],
        signature="valid_signature"
    )

@pytest.fixture
def compromised_mission():
    """Создание скомпрометированной миссии"""
    return Mission(
        waypoints=[GeoPoint(55.0, 37.0), GeoPoint(55.1, 37.1)],
        speed_limits=[50, 50],
        signature="invalid_signature"  # Неправильная подпись
    )

def test_safety_block_compromise_detection(safety_block, compromised_mission):
    """Тест обнаружения компрометации в блоке безопасности"""
    # Отправляем скомпрометированную миссию
    safety_block._set_mission(compromised_mission)
    
    # Проверяем, что скорость установлена в 0
    assert safety_block._speed == 0
    # Проверяем, что направление установлено в 0
    assert safety_block._direction == 0

def test_control_system_stop_on_compromise(control_system, compromised_mission):
    """Тест остановки системы управления при компрометации"""
    # Устанавливаем скомпрометированную миссию
    control_system._set_mission(compromised_mission)
    
    # Проверяем, что система управления остановлена
    assert control_system._quit is True

def test_security_monitor_event_blocking(security_monitor, compromised_mission):
    """Тест блокировки событий монитором безопасности при компрометации"""
    # Создаем тестовое событие
    test_event = Event(
        operation="test_operation",
        parameters={"test": "value"},
        destination="test_destination"
    )
    
    # Проверяем, что событие блокируется
    assert not security_monitor._check_event(test_event)

def test_full_system_compromise(safety_block, control_system, security_monitor, compromised_mission):
    """Тест полной остановки системы при компрометации"""
    # Устанавливаем скомпрометированную миссию
    safety_block._set_mission(compromised_mission)
    
    # Проверяем остановку всех компонентов
    assert safety_block._speed == 0
    assert safety_block._direction == 0
    assert control_system._quit is True
    
    # Проверяем блокировку событий
    test_event = Event(
        operation="test_operation",
        parameters={"test": "value"},
        destination="test_destination"
    )
    assert not security_monitor._check_event(test_event) 