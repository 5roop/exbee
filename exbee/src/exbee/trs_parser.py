from pathlib import Path
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from loguru import logger
from trsproc.parser import TRSParser
from pydantic import BaseModel, Field, field_validator


class Segment(BaseModel):
    xmin: float
    xmax: float
    speaker: str
    content: str

    @field_validator("xmax")
    @classmethod
    def validate_xmax(cls, v, info):
        if v <= info.data["xmin"]:
            raise ValueError("xmax must be greater than xmin")
        return v


class TRS:
    def __init__(self, file: Path | str):
        self.path = Path(file)
        self.doc = etree.fromstring(Path(file).read_bytes())
        self.speakers_raw = self.find_speakers_from_turns()
        self.speaker_table = {
            s.attrib["id"]: s.attrib["name"] for s in self.doc.findall(".//Speaker")
        }
        self.contents = self.get_contents()
        self.speakers = [self.speaker_table[s] for s in self.speakers_raw]
        self.nn = self.get_nn()

    def find_speakers_from_turns(self) -> list[str]:
        """Extracts speakers from tier speaker attribute

        :return list[str]: List of speakers, deduplicated, in order of appearance.
        """
        turns = self.doc.findall(".//Turn")
        turns = [t for t in turns if "speaker" in t.attrib]
        speakers = [t.attrib["speaker"] for t in turns]
        speakers = [i for s in speakers for i in s.split()]
        speakers = list(dict.fromkeys(speakers))
        return speakers

    def get_contents(self):
        """Read trs data and return it in a dictionary
        :return dict: each speaker its own key, values are lists
            of {xmin:, xmax:, content:, speaker:}
        """
        result = dict()
        for speaker in self.speakers_raw:
            result[speaker] = []
        contents = TRSParser(self.path).contents
        for i in list(contents):
            if not contents[i]:
                continue
            if i == 0:
                continue
            if contents[i].get("content", "").strip() == "":
                continue
            content = contents[i]["content"]
            xmin = contents[i]["xmin"]
            xmax = contents[i]["xmax"]
            speaker = contents[i]["speaker"]
            if not content:
                continue
            if "<" in content:
                speakers = contents[i]["speaker"]
                if len(speakers.split()) != len(set(speakers.split())):
                    logger.critical(
                        f"Duplicate speakers appearing! Issue: '{speakers}'. Will proced with garbage data."
                    )
                d = etree.fromstring("<doc>" + content + "</doc>")
                for who in d.findall(".//Who"):
                    j = int(who.attrib["nb"])
                    speaker = contents[i]["speaker"].split()[j - 1]
                    text = who.tail
                    if not text:
                        continue
                    result[speaker] = result[speaker] + [
                        dict(xmin=xmin, xmax=xmax, speaker=speaker, content=text)
                    ]
            else:
                result[speaker] = result[speaker] + [
                    dict(
                        xmin=xmin,
                        xmax=xmax,
                        speaker=speaker,
                        content=content,
                    )
                ]
        old_speakers = list(result.keys())
        for o in old_speakers:
            result[self.speaker_table[o]] = sorted(
                result[o], key=lambda d: float(d["xmin"])
            )
            # Validate:
            for i in result[self.speaker_table[o]]:
                Segment(**i)
            del result[o]
        return result

    def get_nn(self):
        nns = []
        for event in self.doc.findall(".//Event"):
            what = event.attrib["desc"]
            start_s = round(
                float(event.xpath("preceding::Sync[1]")[0].attrib["time"]), 3
            )
            end_s = round(float(event.xpath("following::Sync[1]")[0].attrib["time"]), 3)
            nns.append(
                dict(
                    xmin=start_s,
                    xmax=end_s,
                    speaker="nn",
                    content=what,
                )
            )
        # Validate:
        for nn in nns:
            Segment(**nn)
        return nns
