from pathlib import Path

demo_file = list(Path(".").glob("**/ROG-Dia-GSO-P0005.exb"))[0]

from exbee import EXB

exb = EXB(demo_file)


def test_loading():
    assert exb


def test_finding_speakers():
    assert exb.speakers == ["ROG-dialog-0007", "ROG-dialog-0008"]


def test_finding_timeline():
    assert len(exb.timeline) == 1148


def test_pruning_timeline():
    new_exb = exb.copy()
    new_exb.remove_duplicated_tlis()
    assert exb.timeline == new_exb.timeline


def test_tier_name_getter():
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
