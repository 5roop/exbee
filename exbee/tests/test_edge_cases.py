from pathlib import Path
import pytest

demo_file = list(Path(".").glob("**/ROG-Dia-GSO-P0005.exb"))[0]

from exbee import EXB

exb = EXB(demo_file)


def test_round_timeline():
    """round_timeline should round all timestamps to the specified precision"""
    exb = EXB(demo_file)
    original_times = list(exb.timeline.values())
    exb.round_timeline(decimals=3)  # Already at 3, but should be idempotent
    rounded_times = list(exb.timeline.values())
    for t in rounded_times:
        # All times should have at most 3 decimal places
        assert len(str(t).split(".")[1]) <= 3 if "." in str(t) else True


def test_speakers_from_display_name():
    """find_speakers_from_tier_display_name extracts speakers from display-name attribute"""
    exb = EXB(demo_file)
    speakers = exb.find_speakers_from_tier_display_name()
    assert len(speakers) > 0
    # The names should be prefixes before spaces
    for s in speakers:
        assert len(s) > 0


def test_save_and_reload_roundtrip(tmp_path):
    """Save and re-read the EXB file, verifying structural integrity"""
    exb = EXB(demo_file)
    save_path = tmp_path / "test_output.exb"
    exb.sort_tlis()  # ensure consistent order before saving
    exb.save(save_path)

    # Re-load the saved file
    reloaded = EXB(save_path)
    assert len(reloaded.timeline) == len(exb.timeline)
    assert reloaded.speakers == exb.speakers
    assert reloaded.get_tier_names() == exb.get_tier_names()


def test_remove_duplicated_tlis_exact_duplicates():
    """TLIs with identical times should be deduplicated"""
    exb = EXB(demo_file)
    original_len = len(exb.timeline)
    exb.remove_duplicated_tlis()
    assert len(exb.timeline) <= original_len
    # No two TLIs should have the same time value
    times = list(exb.timeline.values())
    assert all(abs(times[i] - times[i + 1]) > 1e-6 for i in range(len(times) - 1))


@pytest.mark.parametrize("decimals", [0, 1, 2, 3, 4, 5])
def test_round_timeline_with_different_precision(decimals):
    """Should be able to round to different decimal places"""
    exb = EXB(demo_file)
    exb.round_timeline(decimals=decimals)
    for time in exb.timeline.values():
        assert time == round(time, decimals)  # All times are integers now
