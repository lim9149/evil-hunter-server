from core.combat import calculate_damage

def test_damage():
    assert calculate_damage(100) == 120