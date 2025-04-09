from src.communication_gateway import BaseCommunicationGateway
from src.navigation_system import BaseNavigationSystem
from src.control_system import BaseControlSystem
from src.config import CONTROL_SYSTEM_QUEUE_NAME, LOG_ERROR, LOG_INFO
from src.event_types import Event
from src.mission_type import Mission
from src.queues_dir import QueuesDirectory
from queue import Queue

class CommunicationGateway(BaseCommunicationGateway):
    """ класс коммуникационного шлюза """
    
    def _send_mission_to_consumers(self):
        """ отправка маршрутного задания получателям """
        self._log_message(LOG_ERROR, "получен новый маршрут, отправляем в получателям")
        
        # Создаем событие для системы управления
        event = Event(
            source=self.event_source_name,
            destination=CONTROL_SYSTEM_QUEUE_NAME,
            operation="set_mission",
            parameters=self._mission
        )
        
        # Получаем очередь системы управления
        control_q: Queue = self._queues_dir.get_queue(CONTROL_SYSTEM_QUEUE_NAME)
        
        # Отправляем событие
        control_q.put(event)

class NavigationSystem(BaseNavigationSystem):
    """ класс навигационного блока """
    
    def _send_position_to_consumers(self):
        """ отправка координат получателям """
        # Создаем событие для системы управления
        event = Event(
            source=self.event_source_name,
            destination=CONTROL_SYSTEM_QUEUE_NAME,
            operation="position_update",
            parameters=self._position
        )
        
        # Получаем очередь системы управления
        control_q: Queue = self._queues_dir.get_queue(CONTROL_SYSTEM_QUEUE_NAME)
        
        # Отправляем событие
        control_q.put(event)

class ControlSystem(BaseControlSystem):
    """ класс системы управления """
    
    def _send_speed_and_direction_to_consumers(self, speed: float, direction: float):
        """ отправка команд скорости и направления получателям """
        # Создаем события для сервоприводов
        speed_event = Event(
            source=self.event_source_name,
            destination="servos",
            operation="set_speed",
            parameters=speed
        )
        
        direction_event = Event(
            source=self.event_source_name,
            destination="servos",
            operation="set_direction",
            parameters=direction
        )
        
        # Получаем очередь сервоприводов
        servos_q: Queue = self._queues_dir.get_queue("servos")
        
        # Отправляем события
        servos_q.put(speed_event)
        servos_q.put(direction_event)
    
    def _release_cargo(self):
        """ разблокировка грузового отсека """
        # Создаем событие для грузового отсека
        event = Event(
            source=self.event_source_name,
            destination="cargo",
            operation="release_cargo",
            parameters=None
        )
        
        # Получаем очередь грузового отсека
        cargo_q: Queue = self._queues_dir.get_queue("cargo")
        
        # Отправляем событие
        cargo_q.put(event)
    
    def _lock_cargo(self):
        """ блокировка грузового отсека """
        # Создаем событие для грузового отсека
        event = Event(
            source=self.event_source_name,
            destination="cargo",
            operation="lock_cargo",
            parameters=None
        )
        
        # Получаем очередь грузового отсека
        cargo_q: Queue = self._queues_dir.get_queue("cargo")
        
        # Отправляем событие
        cargo_q.put(event) 