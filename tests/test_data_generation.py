from src.data_generation import generate_all


def test_synthetic_data_generates_expected_row_counts():
    frames = generate_all()
    assert len(frames["fleets"]) == 80
    assert len(frames["vehicles"]) == 2000
    assert len(frames["exposure"]) == 48000
    assert len(frames["policies"]) == 80
    assert len(frames["claims"]) == 1500
    assert len(frames["client_interactions"]) == 400


def test_no_negative_premiums():
    frames = generate_all()
    assert (frames["policies"]["written_premium"] >= 0).all()
    assert (frames["policies"]["earned_premium"] >= 0).all()


def test_no_invalid_autonomy_levels():
    frames = generate_all()
    assert frames["fleets"]["autonomy_level"].between(0, 5).all()
    assert frames["vehicles"]["autonomy_level"].between(0, 5).all()
