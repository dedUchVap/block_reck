"""
Измененные компоненты системы для модуля 3:
1. CommunicationGateway - Коммуникационный шлюз
2. NavigationSystem - Система навигации
3. ControlSystem - Система управления

Все компоненты модифицированы для работы с монитором безопасности
"""

from src.communication_gateway import BaseCommunicationGateway
from src.navigation_system import BaseNavigationSystem
from src.control_system import BaseControlSystem
from src.config import (
    CONTROL_SYSTEM_QUEUE_NAME, 
    SAFETY_BLOCK_QUEUE_NAME,
    SERVOS_QUEUE_NAME,
    CARGO_BAY_QUEUE_NAME,
    SECURITY_MONITOR_QUEUE_NAME,
    LOG_ERROR, 
    LOG_INFO
)
from src.event_types import Event
from src.queues_dir import QueuesDirectory
from queue import Queue

# ============================================================================
# КОММУНИКАЦИОННЫЙ ШЛЮЗ (COMMUNICATION GATEWAY)
# ============================================================================

class CommunicationGateway(BaseCommunicationGateway):
    """ 
    Класс коммуникационного шлюза
    
    Отправляет маршрутное задание в систему управления через монитор безопасности
    """
    
    def _send_mission_to_consumers(self):
        """ 
        Отправка маршрутного задания получателям через монитор безопасности
        """
        self._log_message(LOG_ERROR, "получен новый маршрут, отправляем в получателям")
        
        # Создаем событие для системы управления
        event = Event(
            source=self.event_source_name,
            destination=CONTROL_SYSTEM_QUEUE_NAME,
            operation="set_mission",
            parameters=self._mission
        )
        
        # Отправляем событие через монитор безопасности
        security_monitor_q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        security_monitor_q.put(event)

# ============================================================================
# СИСТЕМА НАВИГАЦИИ (NAVIGATION SYSTEM)
# ============================================================================

class NavigationSystem(BaseNavigationSystem):
    """ 
    Класс навигационного блока
    
    Отправляет координаты в систему управления через монитор безопасности
    """
    
    def _send_position_to_consumers(self):
        """ 
        Отправка координат получателям через монитор безопасности
        """
        # Создаем событие для системы управления
        event = Event(
            source=self.event_source_name,
            destination=CONTROL_SYSTEM_QUEUE_NAME,
            operation="position_update",
            parameters=self._position
        )
        
        # Отправляем событие через монитор безопасности
        security_monitor_q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        security_monitor_q.put(event)

# ============================================================================
# СИСТЕМА УПРАВЛЕНИЯ (CONTROL SYSTEM)
# ============================================================================

class ControlSystem(BaseControlSystem):
    """ 
    Класс системы управления
    
    Отправляет команды скорости и направления в ограничитель через монитор безопасности
    """
    
    def _send_speed_and_direction_to_consumers(self, speed: float, direction: float):
        """ 
        Отправка команд скорости и направления в ограничитель через монитор безопасности
        """
        # Создаем события для ограничителя
        speed_event = Event(
            source=self.event_source_name,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation="set_speed",
            parameters=speed
        )
        
        direction_event = Event(
            source=self.event_source_name,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation="set_direction",
            parameters=direction
        )
        
        # Отправляем события через монитор безопасности
        security_monitor_q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        security_monitor_q.put(speed_event)
        security_monitor_q.put(direction_event)
    
    def _release_cargo(self):
        """ 
        Отправка команды разблокировки груза в ограничитель через монитор безопасности
        """
        # Создаем событие для ограничителя
        event = Event(
            source=self.event_source_name,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation="release_cargo",
            parameters=None
        )
        
        # Отправляем событие через монитор безопасности
        security_monitor_q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        security_monitor_q.put(event)
    
    def _lock_cargo(self):
        """ 
        Отправка команды блокировки груза в ограничитель через монитор безопасности
        """
        # Создаем событие для ограничителя
        event = Event(
            source=self.event_source_name,
            destination=SAFETY_BLOCK_QUEUE_NAME,
            operation="lock_cargo",
            parameters=None
        )
        
        # Отправляем событие через монитор безопасности
        security_monitor_q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        security_monitor_q.put(event) 