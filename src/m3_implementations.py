"""
Реализации компонентов для модуля 3:
1. SafetyBlock - Ограничитель для обеспечения ЦБ1 и ЦБ3
2. SecurityMonitor - Монитор безопасности для контроля взаимодействий
"""

from src.safety_block import BaseSafetyBlock
from src.security_monitory import BaseSecurityMonitor
from src.security_policy_type import SecurityPolicy
from src.config import (
    COMMUNICATION_GATEWAY_QUEUE_NAME,
    CONTROL_SYSTEM_QUEUE_NAME,
    NAVIGATION_QUEUE_NAME,
    SAFETY_BLOCK_QUEUE_NAME,
    SERVOS_QUEUE_NAME,
    CARGO_BAY_QUEUE_NAME,
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO
)
from src.event_types import Event
from src.queues_dir import QueuesDirectory
from queue import Queue
import math

# ============================================================================
# ОГРАНИЧИТЕЛЬ (SAFETY BLOCK)
# ============================================================================

class SafetyBlock(BaseSafetyBlock):
    """
    Класс ограничителя безопасности

    Обеспечивает:
    - ЦБ1: соблюдение ограничений скорости и направления
    - ЦБ3: контроль доставки груза только в конечной точке маршрута
    """

    def _set_new_direction(self, direction: float):
        """
        Установка нового направления перемещения с проверкой безопасности

        Проверяет, что запрошенное направление соответствует расчетному
        направлению к следующей точке маршрута
        """
        self._log_message(LOG_INFO, f"текущие координаты: {self._position}")
        self._log_message(LOG_DEBUG, f"маршрутное задание: {self._mission}")
        self._log_message(LOG_DEBUG, f"состояние маршрута: {self._route}")

        # Если маршрут завершен, устанавливаем направление 0
        if self._route.route_finished:
            self._direction = 0
            self._send_direction_to_consumers()
            return

        # Рассчитываем правильное направление к следующей точке
        next_point = self._route.next_point()
        correct_direction = self._calculate_bearing(self._position, next_point)

        # Проверяем, что запрошенное направление близко к правильному
        # Допускаем отклонение до 5 градусов
        direction_diff = abs(direction - correct_direction)
        if direction_diff > 5 and direction_diff < 355:
            self._log_message(LOG_ERROR,
                f"принудительная установка направления! Запрошенное направление {direction}, "
                f"расчётное {correct_direction}")
            # Устанавливаем правильное направление
            self._direction = correct_direction
        else:
            # Направление допустимо
            self._direction = direction

        self._send_direction_to_consumers()

    def _set_new_speed(self, speed: float):
        """
        Установка новой скорости с проверкой безопасности

        Проверяет, что запрошенная скорость не превышает ограничения
        для текущего сегмента маршрута
        """
        # Если маршрут завершен, устанавливаем скорость 0
        if self._route.route_finished:
            self._speed = 0
            self._send_speed_to_consumers()
            return

        # Получаем ограничение скорости для текущего сегмента
        speed_limit = self._route.calculate_speed()

        # Проверяем, что запрошенная скорость не превышает ограничение
        if speed > speed_limit:
            self._log_message(LOG_ERROR,
                f"принудительная установка скорости! Запрошенная скорость {speed}, "
                f"ограничение {speed_limit}")
            # Устанавливаем допустимую скорость
            self._speed = speed_limit
        else:
            # Скорость допустима
            self._speed = speed

        self._send_speed_to_consumers()

    def _lock_cargo(self, _):
        """
        Блокировка грузового отсека

        Разрешаем блокировку в любой момент
        """
        self._send_lock_cargo_to_consumers()

    def _release_cargo(self, _):
        """
        Разблокировка грузового отсека

        Разрешаем только в конечной точке маршрута
        """
        if self._route.route_finished:
            self._log_message(LOG_INFO, "маршрут завершен, разрешаем выгрузку груза")
            self._send_release_cargo_to_consumers()
        else:
            self._log_message(LOG_ERROR, "попытка выгрузки груза вне конечной точки маршрута!")

    def _send_speed_to_consumers(self):
        """ Отправка команды скорости в сервоприводы """
        self._log_message(LOG_DEBUG, "отправляем скорость получателям")
        servos_q_name = SERVOS_QUEUE_NAME
        servos_q: Queue = self._queues_dir.get_queue(servos_q_name)

        # Отправка сообщения с допустимой скоростью
        event_speed = Event(
            source=self.event_source_name,
            destination=servos_q_name,
            operation="set_speed",
            parameters=self._speed
        )
        servos_q.put(event_speed)

    def _send_direction_to_consumers(self):
        """ Отправка команды направления в сервоприводы """
        self._log_message(LOG_DEBUG, "отправляем направление получателям")
        servos_q_name = SERVOS_QUEUE_NAME
        servos_q: Queue = self._queues_dir.get_queue(servos_q_name)

        # Отправка сообщения с допустимым направлением
        event_direction = Event(
            source=self.event_source_name,
            destination=servos_q_name,
            operation="set_direction",
            parameters=self._direction
        )
        servos_q.put(event_direction)

    def _send_lock_cargo_to_consumers(self):
        """ Отправка команды блокировки груза """
        self._log_message(LOG_DEBUG, "отправляем команду блокировки груза")
        cargo_q_name = CARGO_BAY_QUEUE_NAME
        cargo_q: Queue = self._queues_dir.get_queue(cargo_q_name)

        # Отправка сообщения о блокировке груза
        event_lock = Event(
            source=self.event_source_name,
            destination=cargo_q_name,
            operation="lock_cargo",
            parameters=None
        )
        cargo_q.put(event_lock)

    def _send_release_cargo_to_consumers(self):
        """ Отправка команды разблокировки груза """
        self._log_message(LOG_DEBUG, "отправляем команду разблокировки груза")
        cargo_q_name = CARGO_BAY_QUEUE_NAME
        cargo_q: Queue = self._queues_dir.get_queue(cargo_q_name)

        # Отправка сообщения о разблокировке груза
        event_release = Event(
            source=self.event_source_name,
            destination=cargo_q_name,
            operation="release_cargo",
            parameters=None
        )
        cargo_q.put(event_release)

    def _calculate_bearing(self, start, end):
        """
        Расчет направления (азимута) от начальной точки к конечной

        Args:
            start: начальная точка (GeoPoint)
            end: конечная точка (GeoPoint)

        Returns:
            float: направление в градусах (0-360)
        """
        delta_longitude = end.longitude - start.longitude
        x = math.sin(math.radians(delta_longitude)) * math.cos(math.radians(end.latitude))
        y = math.cos(math.radians(start.latitude)) * math.sin(math.radians(end.latitude)) - \
            math.sin(math.radians(start.latitude)) * math.cos(math.radians(end.latitude)) * \
            math.cos(math.radians(delta_longitude))

        initial_bearing_rad = math.atan2(x, y)
        initial_bearing_deg = math.degrees(initial_bearing_rad)
        compass_bearing = (initial_bearing_deg + 360) % 360

        return compass_bearing

# ============================================================================
# МОНИТОР БЕЗОПАСНОСТИ (SECURITY MONITOR)
# ============================================================================

class SecurityMonitor(BaseSecurityMonitor):
    """
    Класс монитора безопасности

    Контролирует допустимость взаимодействий между компонентами системы
    согласно заданной политике безопасности
    """

    def __init__(self, queues_dir):
        super().__init__(queues_dir)
        self._security_policies = set()  # Используем множество вместо словаря
        self._init_set_security_policies()

    def _init_set_security_policies(self):
        """
        Инициализация политик безопасности

        Определяет разрешенные взаимодействия между компонентами системы
        """
        # Базовые политики безопасности
        policies = [
            # Коммуникационный шлюз -> Система управления: установка маршрутного задания
            SecurityPolicy(
                source=COMMUNICATION_GATEWAY_QUEUE_NAME,
                destination=CONTROL_SYSTEM_QUEUE_NAME,
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

            # Система навигации -> Система управления: обновление позиции
            SecurityPolicy(
                source=NAVIGATION_QUEUE_NAME,
                destination=CONTROL_SYSTEM_QUEUE_NAME,
                operation='update_position'),

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
                operation='release_cargo')
        ]

        self.set_security_policies(policies)

    def set_security_policies(self, policies):
        """
        Установка политик безопасности

        Args:
            policies: список политик безопасности
        """
        self._security_policies = set(policies)

    def _check_event(self, event: Event) -> bool:
        """
        Проверка соответствия события политикам безопасности

        Args:
            event: проверяемое событие

        Returns:
            bool: True если событие разрешено, False если запрещено
        """
        # Создаем объект политики для сравнения
        request = SecurityPolicy(
            source=event.source,
            destination=event.destination,
            operation=event.operation
        )

        # Проверяем наличие политики в множестве
        return request in self._security_policies 