from pathlib import Path
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from loguru import logger
from trsproc.parser import TRSParser


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

    def find_speakers_from_turns(self) -> list[str]:
        turns = self.doc.findall(".//Turn")
        turns = [t for t in turns if "speaker" in t.attrib]
        speakers = [t.attrib["speaker"] for t in turns]
        speakers = [i for s in speakers for i in s.split()]
        speakers = list(dict.fromkeys(speakers))
        return speakers

    def get_contents(self):
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
            result[self.speaker_table[o]] = result[o]
            del result[o]
        return result
