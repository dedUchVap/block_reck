from dataclasses import dataclass
import hashlib
import json
from copy import deepcopy
from typing import Tuple
import os
from src.mission_type import Mission, GeoSpecificSpeedLimit
from geopy import Point


class MissionSignature:
    
    
    @staticmethod
    def _serilaze_mission(mission):
        
        list_points = []
        list_speed_limits = []
        dict_mission = {}
        
        for key, value in mission.__dict__.items():
        
            if key == 'signature':
                break
            
            elif key == "waypoints":
                for value_point in value:
                    print(value_point)
                    value_point: Point
                    list_points.append(value_point.format())
                    
                value = list_points
               
            elif key == 'speed_limits':
                for value_speed_limits in value:
                    list_speed_limits.append(value_speed_limits.__dict__)
                    
                value = list_speed_limits
                
            elif key == 'home':
                value = value.format()
                
            dict_mission[key] = value
            
        return dict_mission
    
    @classmethod
    def register_mission_signature(cls, mission: Mission, secret_key) -> Tuple[Mission, str]:
        """
        Подписываем миссию

        """
        serilaze_mission = cls._serilaze_mission(mission)
        # Серилизуем данные в json, использую словарь объекта класса
        mission_json = json.dumps(serilaze_mission, sort_keys=True)

        # Создаем хеш дампа json
        mission_hash = hashlib.sha256(mission_json.encode()).hexdigest()

        # Создаем сигнатуру используя секретный ключ и хеш миссии
        signature = hashlib.sha256((mission_hash + secret_key).encode()).hexdigest()

        # Записываем сигнатуру
        mission.signature = signature
        
        
        print(mission)
        
        return mission


    @classmethod
    def verify_mission(cls, mission: Mission, secret_key):
        """
        Проверка подлинности миссии

        """
        mission_serilaze = cls._serilaze_mission(mission)

        mission_json = json.dumps(mission_serilaze, sort_keys=True)

        mission_hash = hashlib.sha256(mission_json.encode()).hexdigest()

        # Создаем сигнатуру используя секретный ключ и хеш миссии
        signature = hashlib.sha256((mission_hash + secret_key).encode()).hexdigest()

        if signature == mission.signature:
            return True

        return False
