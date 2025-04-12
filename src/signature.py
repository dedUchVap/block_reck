from dataclasses import dataclass
import hashlib
import json
from copy import deepcopy
from typing import Tuple
import os
from src.mission_type import Mission, GeoSpecificSpeedLimit
from geopy import Point
from typing import Dict


class MissionSignature:

    @staticmethod
    def _serilaze_mission(mission) -> Dict:
        """
        Сериализация миссии

        Args:
            mission (Mission): object

        Returns:
            dict: Объект который можно сериализовать

        """
        # Список с точками из миссии
        list_points = []

        # Список с лимитами по скорости
        list_speed_limits = []

        # Словарь который вернет функция
        dict_mission = {}

        # Проходимся по объекту миссии
        for key, value in mission.__dict__.items():

            if key == "signature":
                break

            elif key == "waypoints":
                for value_point in value:
                    print(value_point)
                    value_point: Point
                    list_points.append(value_point.format())

                value = list_points

            elif key == "speed_limits":
                for value_speed_limits in value:
                    list_speed_limits.append(value_speed_limits.__dict__)

                value = list_speed_limits

            elif key == "home":
                value = value.format()

            dict_mission[key] = value

        return dict_mission

    @classmethod
    def register_mission_signature(
        cls, mission: Mission, secret_key
    ) -> Tuple[Mission, str]:
        """
        Добавляем сигнатуру миссии

        Args:
            mission (Mission): object
            secret_key (str): Секретный ключ, для создания подписи, лучше его никому не показывать

        Returns:
            Mission: добавляется сигнатура в объект

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

        return mission

    @classmethod
    def verify_mission(cls, mission: Mission, secret_key):
        """
        Проверка миссии на изменения

        Args:
            mission (Mission): объект
            secret_key (str): Секретный ключ, для создания подписи, лучше его никому не показывать

        Returns:
            bool: Возвращает булево значене, если миссия не изменилась то True
        """
        # Серилизация миссии
        mission_serilaze = cls._serilaze_mission(mission)

        # Преобразование в json
        mission_json = json.dumps(mission_serilaze, sort_keys=True)

        # Создаем хеш
        mission_hash = hashlib.sha256(mission_json.encode()).hexdigest()

        # Создаем сигнатуру используя секретный ключ и хеш миссии
        signature = hashlib.sha256((mission_hash + secret_key).encode()).hexdigest()

        # Проверяем совпадает ли сигнатура
        if signature == mission.signature:
            return True

        return False
