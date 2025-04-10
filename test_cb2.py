""" Тестовый пример работы механизма контроля аутентичности маршрутного задания (ЦБ2) """

from src.cb2_implementation import DigitalSignature, MissionPlannerCB2, CommunicationGatewayCB2, SafetyBlockCB2
from src.mission_type import Mission
from src.queues_dir import QueuesDirectory
from geopy import Point

def test_digital_signature():
    """ Тест работы механизма цифровой подписи """
    print("\n=== Тест механизма цифровой подписи ===")
    
    # Создаем тестовое маршрутное задание
    route = [
        Point(55.751244, 37.618423),  # Москва
        Point(59.934280, 30.335099),  # Санкт-Петербург
        Point(56.326797, 44.006516)   # Нижний Новгород
    ]
    cargo = {"type": "test", "weight": 100}
    mission = Mission(route=route, cargo=cargo)
    
    print("\nИсходное задание:")
    print(f"Маршрут: {[f'({p.latitude}, {p.longitude})' for p in mission.route]}")
    print(f"Груз: {mission.cargo}")
    
    # Создаем экземпляр для подписания
    signer = DigitalSignature("private_key_123")
    
    # Подписываем задание
    signed_mission, signature = signer.sign_mission(mission.to_dict())
    print("\nПодписанное задание:")
    print(f"Подпись: {signature}")
    print(f"Данные: {signed_mission}")
    
    # Создаем экземпляр для проверки
    verifier = DigitalSignature("public_key_123")
    
    # Проверяем подпись
    is_valid = verifier.verify_mission(signed_mission, "public_key_123")
    print(f"\nПроверка подписи: {'успешно' if is_valid else 'ошибка'}")
    
    # Пробуем подделать задание
    print("\n=== Попытка подделки задания ===")
    fake_mission = signed_mission.copy()
    fake_mission["route"][0] = [90.0, 180.0]  # Изменяем первую точку маршрута
    
    # Проверяем подпись подделанного задания
    is_valid = verifier.verify_mission(fake_mission, "public_key_123")
    print(f"Проверка подписи подделанного задания: {'успешно' if is_valid else 'ошибка'}")

def test_mission_planner():
    """ Тест работы планировщика с цифровой подписью """
    print("\n=== Тест работы планировщика ===")
    
    # Создаем тестовое маршрутное задание
    route = [
        Point(55.751244, 37.618423),  # Москва
        Point(59.934280, 30.335099)   # Санкт-Петербург
    ]
    mission = Mission(route=route)
    
    # Создаем планировщик
    queues_dir = QueuesDirectory()
    planner = MissionPlannerCB2(queues_dir)
    
    # Подписываем и отправляем задание
    print("\nПланировщик подписывает и отправляет задание:")
    signed_mission, signature = planner._signer.sign_mission(mission.to_dict())
    print(f"Подпись: {signature}")
    print(f"Данные: {signed_mission}")

def test_communication_gateway():
    """ Тест работы коммуникационного шлюза с проверкой подписи """
    print("\n=== Тест работы коммуникационного шлюза ===")
    
    # Создаем тестовое маршрутное задание
    route = [
        Point(55.751244, 37.618423),  # Москва
        Point(59.934280, 30.335099)   # Санкт-Петербург
    ]
    mission = Mission(route=route)
    
    # Создаем шлюз
    queues_dir = QueuesDirectory()
    gateway = CommunicationGatewayCB2(queues_dir)
    
    # Подписываем задание
    signer = DigitalSignature("private_key_123")
    signed_mission, _ = signer.sign_mission(mission.to_dict())
    
    # Проверяем подпись
    print("\nШлюз проверяет подпись задания:")
    is_valid = gateway._verifier.verify_mission(signed_mission, "mission_planner_public_key")
    print(f"Проверка подписи: {'успешно' if is_valid else 'ошибка'}")

def test_safety_block():
    """ Тест работы блока безопасности с проверкой подписи """
    print("\n=== Тест работы блока безопасности ===")
    
    # Создаем тестовое маршрутное задание
    route = [
        Point(55.751244, 37.618423),  # Москва
        Point(59.934280, 30.335099)   # Санкт-Петербург
    ]
    mission = Mission(route=route)
    
    # Создаем блок безопасности
    queues_dir = QueuesDirectory()
    safety = SafetyBlockCB2(queues_dir)
    
    # Подписываем задание
    signer = DigitalSignature("private_key_123")
    signed_mission, _ = signer.sign_mission(mission.to_dict())
    
    # Проверяем подпись
    print("\nБлок безопасности проверяет подпись задания:")
    is_valid = safety._verifier.verify_mission(signed_mission, "mission_planner_public_key")
    print(f"Проверка подписи: {'успешно' if is_valid else 'ошибка'}")

if __name__ == "__main__":
    print("=== Демонстрация работы механизма контроля аутентичности маршрутного задания (ЦБ2) ===")
    test_digital_signature()
    test_mission_planner()
    test_communication_gateway()
    test_safety_block() 