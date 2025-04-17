from src.mission_type import Mission, GeoSpecificSpeedLimit
from geopy import Point
import json
import hashlib
from copy import deepcopy

class MissionSignature:

    def __serilaze_mission(mission) -> dict:

        mission_dict = {}

        points_list = []

        speed_limits = []

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

    @classmethod
    def signature_mission(cls, mission: Mission, secret_key: str) -> Mission:
        mission_serilaze = cls.__serilaze_mission(mission=mission)
        
        mission_copy = deepcopy(mission)
        
        signature = hashlib.sha256(mission_serilaze + secret_key.encode()).hexdigest()
        
        mission_copy.signature = signature
        
        return mission_copy

    @classmethod
    def verify_signature(cls, mission: Mission, secret_key: str) -> Mission:
        mission_serilaze = cls.__serilaze_mission(mission=mission)
        
        mission_copy = deepcopy(mission)
        
        signature = hashlib.sha256(mission_serilaze + secret_key.encode()).hexdigest()
        
        if (mission_copy.signature != signature):
            return False
        
        return True

mission = Mission(
    home=Point(31, 48),
    waypoints=[Point(31, 33), Point(35, 33)],
    speed_limits=[GeoSpecificSpeedLimit(0, 30)],
    armed=True,
)
mission_with_signature = MissionSignature.signature_mission(mission, secret_key="ffaf")
print(MissionSignature.verify_signature(mission_with_signature, secret_key='fff'))
