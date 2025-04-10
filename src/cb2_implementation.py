""" Реализация механизма контроля аутентичности маршрутного задания (ЦБ2) """

import hashlib
import json
from typing import Dict, Any, Tuple, List, Optional
from geopy import Point as GeoPoint
from multiprocessing import Queue, Process
from queue import Empty

from src.queues_dir import QueuesDirectory
from src.event_types import Event, ControlEvent
from src.mission_type import Mission
from src.config import (
    CONTROL_SYSTEM_QUEUE_NAME, LOG_ERROR, LOG_INFO, 
    SECURITY_MONITOR_QUEUE_NAME, LOG_DEBUG, SERVOS_QUEUE_NAME, 
    CARGO_BAY_QUEUE_NAME, DEFAULT_LOG_LEVEL, COMMUNICATION_GATEWAY_QUEUE_NAME
)

class DigitalSignature:
    """ класс для работы с цифровой подписью """
    
    def __init__(self, private_key: str):
        """ инициализация с приватным ключом """
        self._private_key = private_key
        
    def sign_mission(self, mission: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """ подписание маршрутного задания
        
        Args:
            mission: маршрутное задание для подписания
            
        Returns:
            Tuple[Dict[str, Any], str]: подписанное задание и подпись
        """
        # Создаем копию задания для подписания
        mission_to_sign = mission.copy()
        
        # Удаляем существующую подпись, если есть
        mission_to_sign.pop('signature', None)
        
        # Сериализуем задание в JSON
        mission_json = json.dumps(mission_to_sign, sort_keys=True)
        
        # Создаем хеш задания
        mission_hash = hashlib.sha256(mission_json.encode()).hexdigest()
        
        # Создаем подпись (в реальной системе здесь была бы криптография)
        signature = hashlib.sha256((mission_hash + self._private_key).encode()).hexdigest()
        
        # Добавляем подпись в задание
        mission['signature'] = signature
        
        return mission, signature
        
    def verify_mission(self, mission: Dict[str, Any], public_key: str) -> bool:
        """ проверка подписи маршрутного задания
        
        Args:
            mission: подписанное маршрутное задание
            public_key: публичный ключ для проверки
            
        Returns:
            bool: True если подпись верна, False иначе
        """
        # Получаем подпись из задания
        signature = mission.get('signature')
        if not signature:
            return False
            
        # Создаем копию задания без подписи
        mission_to_verify = mission.copy()
        mission_to_verify.pop('signature')
        
        # Сериализуем задание в JSON
        mission_json = json.dumps(mission_to_verify, sort_keys=True)
        
        # Создаем хеш задания
        mission_hash = hashlib.sha256(mission_json.encode()).hexdigest()
        
        # Проверяем подпись (в реальной системе здесь была бы криптография)
        expected_signature = hashlib.sha256((mission_hash + public_key).encode()).hexdigest()
        
        return signature == expected_signature

class MissionPlannerCB2(Process):
    """ класс планировщика маршрутных заданий с поддержкой ЦБ2 """
    log_prefix = "[PLANNER]"
    event_source_name = "planner"
    
    def __init__(self, queues_dir: QueuesDirectory, log_level=DEFAULT_LOG_LEVEL):
        super().__init__()
        self._queues_dir = queues_dir
        self._events_q = Queue()
        self._queues_dir.register(queue=self._events_q, name=self.event_source_name)
        self._quit = False
        self._control_q = Queue()
        self._recalc_interval_sec = 0.1
        self.log_level = log_level
        self._mission: Optional[Mission] = None
        self._signer = DigitalSignature("mission_planner_private_key")
        
    def _log_message(self, criticality: int, message: str):
        """ логирование сообщений """
        if criticality <= self.log_level:
            print(f"{self.log_prefix} {message}")
            
    def _send_mission_to_consumers(self):
        """ отправка маршрутного задания получателям с подписью """
        self._log_message(LOG_DEBUG, "отправляем маршрутное задание получателям")
        
        # Подписываем задание
        signed_mission, signature = self._signer.sign_mission(self._mission.to_dict())
        
        # Создаем событие для коммуникационного шлюза
        event = Event(
            source=self.event_source_name,
            destination=COMMUNICATION_GATEWAY_QUEUE_NAME,
            operation="set_mission",
            parameters=signed_mission
        )
        
        # Отправляем событие
        communication_q: Queue = self._queues_dir.get_queue(COMMUNICATION_GATEWAY_QUEUE_NAME)
        communication_q.put(event)

class CommunicationGatewayCB2(Process):
    """ класс коммуникационного шлюза с поддержкой ЦБ2 """
    log_prefix = "[COMMUNICATION]"
    event_source_name = "communication"
    
    def __init__(self, queues_dir: QueuesDirectory, log_level=DEFAULT_LOG_LEVEL):
        super().__init__()
        self._queues_dir = queues_dir
        self._events_q = Queue()
        self._queues_dir.register(queue=self._events_q, name=self.event_source_name)
        self._quit = False
        self._control_q = Queue()
        self._recalc_interval_sec = 0.1
        self.log_level = log_level
        self._mission: Optional[Mission] = None
        self._verifier = DigitalSignature("mission_planner_public_key")
        
    def _log_message(self, criticality: int, message: str):
        """ логирование сообщений """
        if criticality <= self.log_level:
            print(f"{self.log_prefix} {message}")
            
    def _set_mission(self, mission_dict: Dict[str, Any]):
        """ установка маршрутного задания с проверкой подписи """
        # Проверяем подпись задания
        if not self._verifier.verify_mission(mission_dict, "mission_planner_public_key"):
            self._log_message(LOG_ERROR, "получено задание с неверной подписью")
            return
            
        # Если подпись верна, устанавливаем задание
        self._mission = Mission.from_dict(mission_dict)
        self._send_mission_to_consumers()

class SafetyBlockCB2(Process):
    """ класс блока безопасности с поддержкой ЦБ2 """
    log_prefix = "[SAFETY]"
    event_source_name = "safety"
    
    def __init__(self, queues_dir: QueuesDirectory, log_level=DEFAULT_LOG_LEVEL):
        super().__init__()
        self._queues_dir = queues_dir
        self._events_q = Queue()
        self._queues_dir.register(queue=self._events_q, name=self.event_source_name)
        self._quit = False
        self._control_q = Queue()
        self._recalc_interval_sec = 0.1
        self.log_level = log_level
        self._verifier = DigitalSignature("mission_planner_public_key")
        
    def _log_message(self, criticality: int, message: str):
        """ логирование сообщений """
        if criticality <= self.log_level:
            print(f"{self.log_prefix} {message}")
            
    def _check_mission(self, mission_dict: Dict[str, Any]) -> bool:
        """ проверка маршрутного задания на безопасность и подлинность """
        # Проверяем подпись задания
        if not self._verifier.verify_mission(mission_dict, "mission_planner_public_key"):
            self._log_message(LOG_ERROR, "получено задание с неверной подписью")
            return False
            
        # Если подпись верна, проверяем безопасность
        mission = Mission.from_dict(mission_dict)
        return self._check_route_safety(mission.route)
        
    def _check_route_safety(self, route: List[GeoPoint]) -> bool:
        """ проверка безопасности маршрута """
        # Здесь должна быть реальная проверка безопасности маршрута
        return True 