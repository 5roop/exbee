from pathlib import Path
from exbee import EXB

demo_file = list(Path(".").glob("**/duplicated_tier.exb"))[0]
okfile = list(Path(".").glob("**/ROG-Dia-GSO-P0005.exb"))[0]


dup = EXB(demo_file)


def test_duplicated_ids():
    assert dup.test_tier_id_unique() == False


def test_duplicated_display_names():
    assert dup.test_tier_display_name_unique() == False


def test_removal_of_duplicated_tiers():
    ddup = dup.copy()
    ddup.remove_duplicated_tiers()
    tiers_after_dedup = ddup.doc.xpath(".//tier")
    tiers_non_dup = EXB(okfile).doc.xpath(".//tier")
    for i, j in zip(tiers_after_dedup, tiers_non_dup):
        assert i.attrib == j.attrib
        assert len(i.findall(".//event")) == len(j.findall(".//event"))
