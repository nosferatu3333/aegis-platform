from scripts.release_acceptance import run_acceptance


def test_formal_mvp_acceptance_scenarios_pass():
    report = run_acceptance()

    assert report["accepted"] is True
    assert report["scenario_count"] == 5
    assert {item["actual_status"] for item in report["scenarios"]} == {
        "analyzed",
        "completed",
        "paused",
        "denied",
        "failed",
    }
    assert report["real_world_effects_verified"] is False
