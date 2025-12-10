from pathlib import Path

demo_file = list(Path(".").glob("**/ROG-Dia-GSO-P0005.exb"))[0]

from exbee import EXB

exb = EXB(demo_file)


def test_loading():
    assert exb


def test_finding_speakers():
    exb = EXB(demo_file)
    assert exb.speakers == ["ROG-dialog-0007", "ROG-dialog-0008"]


def test_finding_timeline():
    exb = EXB(demo_file)
    assert len(exb.timeline) == 1148


def test_pruning_timeline():
    new_exb = exb.copy()
    new_exb.remove_duplicated_tlis()
    assert exb.timeline == new_exb.timeline


def test_tier_name_getter():
    exb = EXB(demo_file)
    assert exb.get_tier_names() == [
        "ROG-dialog-0007 [colloq]",
        "ROG-dialog-0007 [norm]",
        "ROG-dialog-0007 [dialogueActsIsoDimension]",
        "ROG-dialog-0007 [dialogueActsIsoFunction]",
        "ROG-dialog-0007 [sentimentCurated]",
        "ROG-dialog-0007 [sentimentAnnotated]",
        "ROG-dialog-0007 [normSeg]",
        "ROG-dialog-0007 [colloqSeg]",
        "ROG-dialog-0008 [colloq]",
        "ROG-dialog-0008 [norm]",
        "ROG-dialog-0008 [dialogueActsIsoDimension]",
        "ROG-dialog-0008 [dialogueActsIsoFunction]",
        "ROG-dialog-0008 [sentimentCurated]",
        "ROG-dialog-0008 [sentimentAnnotated]",
        "ROG-dialog-0008 [normSeg]",
        "ROG-dialog-0008 [colloqSeg]",
        "[nn]",
    ]


def test_unhiding_tiers():
    exb = EXB(demo_file)
    tiers = [
        t
        for t in exb.doc.findall(".//tier")
        if t.find(f".//ud-information[@attribute-name='exmaralda:hidden']") is not None
    ]
    assert len(tiers) == 1
    exb.remove_unused_attributes()
    tiers = [
        t
        for t in exb.doc.findall(".//tier")
        if t.find(f".//ud-information[@attribute-name='exmaralda:hidden']") is not None
    ]
    assert len(tiers) == 0
    2 + 2


def test_global_trailing_space_addition():
    exb = EXB(demo_file)
    original_len = sum([len(i.text.split()) for i in exb.doc.findall(".//event")])
    exb.add_trailing_spaces()
    text_after_one_pass = "".join([i.text for i in exb.doc.findall(".//event")])
    exb.add_trailing_spaces()
    text_after_second_pass = "".join([i.text for i in exb.doc.findall(".//event")])
    assert text_after_one_pass == text_after_second_pass
    assert original_len == len(text_after_one_pass.split())
    assert original_len == len(text_after_second_pass.split())


def test_single_tier_trailing_space_addition():
    exb = EXB(demo_file)
    tier_name = exb.get_tier_names()[0]
    tier = exb.doc.find(f".//tier[@display-name='{tier_name}']")
    original_text = [i.text for i in tier.findall(".//event")]
    exb.add_trailing_spaces_to_tier(tier)
    tier = exb.doc.find(f".//tier[@display-name='{tier_name}']")
    new_text = [i.text for i in tier.findall(".//event")]

    assert len(original_text) == len(new_text)
    for o, n in zip(original_text, new_text):
        assert o.strip() == n.strip()
        assert n.endswith(" ")


def test_adding_timeline_elements():
    exb = EXB(demo_file)
    id = exb.add_to_timeline(0.222)
    exb.sort_tlis()
    assert list(exb.timeline.keys())[1] == id
    assert exb.timeline[id] == 0.222
