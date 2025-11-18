# exbee
A small python package for wrangling EXB files


## Installation

Via pip: `pip install "git+https://github.com/5roop/exbee.git#subdirectory=exbee"`

## Exploratory usage:

```python
from exbee import EXB
exb = EXB("ROG-Dia-GSO-P0005.exb")

# Get all tier display names:
exb.get_tier_names()
# Returns:
[
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

# Get speakers present:
exb.speakers
# Returns:
["ROG-dialog-0007", "ROG-dialog-0008"]


# Get timeline:
exb.timeline
# Returns:
{'T0': 0.0, 'T0-555': 0.555, 'T2': 1.1333328588017242, 'T3-017': 3.017,
 'T3': 3.2866652905249993, 'T4': 4.019998316808468, 'T5-403': 5.403, ...}

# Get wavfile:
wavpath = exb.wavfile_raw # Wav, as listed in the EXB

# Get its absolute location
wavpath_absolute = exb.wavfile_abs

# Saving the EXB to a new file:
exb.save("saved_files/out.exb")
# This removes duplicated tli elements, unused attributes such as AutoSave, and
# runs xmllint on the file, saving it in UTF8.

```

## Accessing XML contents

exb.doc contains the data from the XML file, as parsed with `lxml.etree` library.
This means a specific tier can be accessed as

```python
tier = exb.doc.find(".//tier[@display-name='ROG-dialog-0008 [colloqSeg]']")
```

and all its events can be extracted as:

```python
elements = tier.findall(".//event")
```



