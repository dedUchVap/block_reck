from multiprocessing import Queue, Process
from src.queues_dir import QueuesDirectory
import secrets
import string
from geopy import Point
from mission_type import GeoSpecificSpeedLimit, Mission
import json
import hashlib
from copy import deepcopy
from src.event_types import Event, ControlEvent
from src.config import CRITICALITY_STR, LOG_ERROR, LOG_DEBUG, LOG_INFO, VERIFY_MISSION_QUEUE_NAME, SAFETY_BLOCK_QUEUE_NAME, PLANNER_QUEUE_NAME, SECURITY_MONITOR_QUEUE_NAME

class Verify(Process):
    
    event_source_name = VERIFY_MISSION_QUEUE_NAME
    
    def __init__(self, queues_dir: QueuesDirectory):
        
        string_list = string.ascii_letters + string.ascii_lowercase + string.ascii_uppercase
        
        super().__init__()
        
        self._queues_dir = queues_dir
        self._events_q = Queue()
        self._events_q_name = self.event_source_name
        
        self._queues_dir.register(self._events_q, self._events_q_name)
        
        self.__secret_key = ''.join(secrets.choice(string_list) for _ in range(64))
        
        self._quit = False
        
        self._handler_event: dict = {'verify': self._verify_signature, 'signature': self._signature_mission}
        
        self.log_prefix = "VERIFY_MISSION"
        
        self._log_message(LOG_INFO, 'Создан компонент верификации миссии')
    
    
    def _log_message(self, criticality: int, message: str):
        """_log_message печатает сообщение заданного уровня критичности

        Args:
            criticality (int): уровень критичности
            message (str): текст сообщения
        """
        if criticality <= self.log_level:
            print(f"[{CRITICALITY_STR[criticality]}]{self.log_prefix} {message}")
    
    def __serilaze_mission(self, mission: Mission) -> str | None:
        """
        Сериализируем миссию здесь
        
        Args:
            mission (Mission): миссия
            
        Returns:
            str: возвращаем строку при успешной сериализации
            None: при получении ошибки вовзращаем объект класса NoneType
        """
        try:
            
            # Словарь для хранения сериализирумыех объектов python
            mission_dict = {}

            # Списки для точек маршрута и лимтов скорости
            points_list = []    # Список точек
            speed_limits = []   # Список огрничений скорости

            # Проходимся по словарю получаему благодаря методу __dict__
            for key, value in mission.__dict__.items():
                if key == "signature":
                    continue
                if key == "waypoints":
                    for value_point in value:
                        value_point: Point
                        points_list.append(value_point.format())

                    mission_dict[key] = points_list

                elif key == "home":
                    value: Point
                    mission_dict[key] = value.format()

                elif key == "speed_limits":
                    for value_speed_limit in value:
                        value_speed_limit: GeoSpecificSpeedLimit
                        speed_limits.append({'speed_limit': value_speed_limit.speed_limit, 'waypoint_index': value_speed_limit.waypoint_index})

                    mission_dict[key] = speed_limits

            mission_serilaze = json.dumps(mission_dict, sort_keys=True).encode()
            return mission_serilaze
        
        # В случае ошибки возвращаем None
        except Exception as e:
            self._log_message(LOG_ERROR, 'Ошибка в сериализации миссии, текст ошибки: ' + e)
            return None
    
    def _signature_mission(self, mission: Mission) -> Mission | False:
        """
        Добавляем миссии цифровую подпись
        
        Args:
            mission (Mission): объект миссии
            
        Returns:
            Mission: возвращаем объект миссии с цифровой подписью если все впорядке
            False: при возникновении ошибки мы возвращаем False
        """
        result = None
        mission_serilaze = self.__serilaze_mission(mission=mission)
        
        if isinstance(mission_serilaze, None):
            return False
        
        mission_copy = deepcopy(mission)

        signature = hashlib.sha256(mission_serilaze + self.__secret_key.encode()).hexdigest()
        
        mission_copy.signature = signature
        
        return mission_copy

    
    def _verify_signature(self, mission: Mission) -> bool:
        """
        Проверяем цифровую подпись
        
        Args:
            mission (Mission): объект миссии
            
        Returns:
            True: если все впорядке вовзращаем True
            False: при возникновении ошибки мы возвращаем False
        """
        result = None
        mission_serilaze = self.__serilaze_mission(mission=mission)
        
        if isinstance(mission_serilaze, None):
            return False
        
        mission_copy = deepcopy(mission)
        
        signature = hashlib.sha256(mission_serilaze + self.__secret_key.encode()).hexdigest()
        
        if (mission_copy.signature != signature):
            return False
        
        return True
    
    
    def _handler_event(self):
        try:
            event: Event = self._events_q.get(timeout=5)
            if not isinstance(event, Event):
                self._log_message(LOG_ERROR, 'Передан неверный объект, нужно передать событие')
                return
            operation = self._handler_event.get(event.operation)
            if not operation:
                self._log_message(LOG_ERROR, 'Данной операции не существует')
            operation(event.parameters)
        except Exception as e:
            self._log_message(LOG_ERROR, 'Произошла ошибка в обработке события, сообщение ошибки: ' + e)
            return
    
    
    def send_result_verify_to_safet(self, result: bool):
        """
        Метод для отправки результата проверки миссии в блок безопасности
        
        Args:
            result (bool): булево значение
        """
        
        event = Event(self.event_source_name,
                      SAFETY_BLOCK_QUEUE_NAME,
                      operation='verify_mission_result',
                      parameters=result)
        
        security_monitor_q: Queue = self._queues_dir.get_queue(SECURITY_MONITOR_QUEUE_NAME)
        
        security_monitor_q.put(event)
              
    def run(self):
        while not self._quit:
            try:
                self._handler_event()
            except Exception as e:
                self._log_message(LOG_ERROR, 'Произошла ошибка в цикле обработки событий, сообщение ошибки: ' + e)