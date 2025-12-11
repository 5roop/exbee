from pathlib import Path

demo_file = list(Path(".").glob("**/ROG-Dia-GSO-P0005-std.trs"))[0]

from exbee import TRS


def test_loading():
    trs = TRS(demo_file)
    2 + 2


def test_sample_instances():
    trs = TRS(demo_file)
    assert trs.speakers_raw == ["spk1", "spk2"]
    assert trs.speakers == ["ROG-dialog-0007", "ROG-dialog-0008"]
    assert (
        trs.contents["ROG-dialog-0007"][2]["content"]
        == "Koliko cajta ... koliko cajta bi bila tam?"
    )

    assert trs.contents["ROG-dialog-0007"] == sorted(
        trs.contents["ROG-dialog-0007"], key=lambda d: d["xmin"]
    )
