""" тесты монитора безопасности """
from src.config import CARGO_BAY_QUEUE_NAME, COMMUNICATION_GATEWAY_QUEUE_NAME, \
    CONTROL_SYSTEM_QUEUE_NAME, SAFETY_BLOCK_QUEUE_NAME, NAVIGATION_QUEUE_NAME, SERVOS_QUEUE_NAME
from src.event_types import Event
from src.security_policy_type import SecurityPolicy


def test_security_policies(security_monitor):
    """ проверка политик безопасности """

        # шаг 3. Добавление новой политики безопасности и повторная проверка запроса
    policies = security_monitor._security_policies
    # pylint: disable=protected-access
    policies.extend([
        # Коммуникационный шлюз -> Система управления: установка маршрутного задания
        SecurityPolicy(
            source=COMMUNICATION_GATEWAY_QUEUE_NAME,
            destination=CONTROL_SYSTEM_QUEUE_NAME,
            operation='set_mission'),

        # Коммуникационный шлюз -> Огрначительный блок: установка маршрутного задания
        SecurityPolicy(
            source=COMMUNICATION_GATEWAY_QUEUE_NAME,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation='set_mission'), 

        # Система управления -> Ограничитель: установка скорости
        SecurityPolicy(
            source=CONTROL_SYSTEM_QUEUE_NAME,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation='set_speed'),
            
        # Система управления -> Ограничитель: установка направления
        SecurityPolicy(
            source=CONTROL_SYSTEM_QUEUE_NAME,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation='set_direction'),

        # Система Навигации -> Ограничетльный блок: установка направления
        SecurityPolicy(
            source=NAVIGATION_QUEUE_NAME,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation='position_update'),

        # Система навигации -> Блок Управления: установка направления
        SecurityPolicy(
            source=NAVIGATION_QUEUE_NAME,
            destination=CONTROL_SYSTEM_QUEUE_NAME,
            operation='position_update'),

        # Система управления -> Ограничитель: блокировка груза
        SecurityPolicy(
            source=CONTROL_SYSTEM_QUEUE_NAME,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation='lock_cargo'),
            
        # Система управления -> Ограничитель: разблокировка груза
        SecurityPolicy(
            source=CONTROL_SYSTEM_QUEUE_NAME,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation='release_cargo'),
            
        # Ограничитель -> Сервоприводы: установка скорости
        SecurityPolicy(
            source=SAFETY_BLOCK_QUEUE_NAME,
            destination=SERVOS_QUEUE_NAME,
            operation='set_speed'),
            
        # Ограничитель -> Сервоприводы: установка направления
        SecurityPolicy(
            source=SAFETY_BLOCK_QUEUE_NAME,
            destination=SERVOS_QUEUE_NAME,
            operation='set_direction'),
            
        # Ограничитель -> Грузовой отсек: блокировка груза
        SecurityPolicy(
            source=SAFETY_BLOCK_QUEUE_NAME,
            destination=CARGO_BAY_QUEUE_NAME,
            operation='lock_cargo'),
            
        # Ограничитель -> Грузовой отсек: разблокировка груза
        SecurityPolicy(
            source=SAFETY_BLOCK_QUEUE_NAME,
            destination=CARGO_BAY_QUEUE_NAME,
            operation='release_cargo'),
    ]) 


    security_monitor.set_security_policies(policies=policies)
    # шаг 2. Проверка допустимого по архитектуре, но не допустимого политиками запроса
    event = Event(source=CONTROL_SYSTEM_QUEUE_NAME,
                  destination=SAFETY_BLOCK_QUEUE_NAME,
                  operation="set_speed",
                  parameters=None)

    authorized = security_monitor._check_event(             # pylint: disable=protected-access
        event=event)  # pylint: disable=protected-access
    
    assert authorized

    # шаг 4. Контрольная проверка неразрешённого запроса
    event = Event(source=COMMUNICATION_GATEWAY_QUEUE_NAME,
                  destination=CARGO_BAY_QUEUE_NAME,
                  operation="set_mission",
                  parameters=None)

    authorized = security_monitor._check_event(             # pylint: disable=protected-access
        event=event)  # pylint: disable=protected-access

    assert authorized is False

    event = Event(source=COMMUNICATION_GATEWAY_QUEUE_NAME,
                  destination=SAFETY_BLOCK_QUEUE_NAME,
                  operation="set_mission",
                  parameters=None)

    authorized = security_monitor._check_event(             # pylint: disable=protected-access
        event=event)  # pylint: disable=protected-access

    assert authorized

    event = Event(source=NAVIGATION_QUEUE_NAME,
                  destination=SAFETY_BLOCK_QUEUE_NAME,
                  operation="position_update",
                  parameters=None)

    authorized = security_monitor._check_event(             # pylint: disable=protected-access
        event=event)  # pylint: disable=protected-access

    assert authorized

    event = Event(source=NAVIGATION_QUEUE_NAME,
                  destination=CONTROL_SYSTEM_QUEUE_NAME,
                  operation="position_update",
                  parameters=None)

    authorized = security_monitor._check_event(             # pylint: disable=protected-access
        event=event)  # pylint: disable=protected-access

    assert authorized
