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
        self.contents_dump = self.parse_into_contents()
        self.contents = self.postprocess_dump()
        self.speakers = [self.speaker_table[s] for s in self.speakers_raw]

    def find_speakers_from_turns(self) -> list[str]:
        """Extracts speakers from tier speaker attribute

        :return list[str]: List of speakers, deduplicated, in order of appearance.
        """
        turns = self.doc.findall(".//Turn")
        turns = [t for t in turns if "speaker" in t.attrib]
        speakers = [t.attrib["speaker"] for t in turns]
        speakers = [i for s in speakers for i in s.split()]
        # speakers = [s for s in speakers if self.doc.find(f".//Turn[@speaker='{s}']")]
        speakers = list(dict.fromkeys(speakers))
        return speakers

    @staticmethod
    def fragment_whos(doc):
        who_elements = doc.findall(".//Who")
        results = []

        parts = []
        current_part = []

        for node in doc.iter():
            if node == doc:  # Skip root element
                continue

            if node.tag == "Who":
                if current_part:
                    parts.append("\n".join(current_part).strip())
                    current_part = []

            current_part.append(
                etree.tostring(node, encoding="unicode", with_tail=True).strip()
            )

        if current_part:
            parts.append("\n".join(current_part).strip())

        parts = [p for p in parts if p.strip()]
        return parts

    def parse_into_contents(self):
        doc = self.doc
        results = []
        turns = doc.findall(".//Turn")
        events = doc.findall(".//Event")
        for e in events:
            assert e.getparent().tag == "Turn"
        for turn in turns:
            speakers = turn.get("speaker", "").split()
            turn_start = float(turn.get("startTime"))
            turn_end = float(turn.get("endTime"))
            if not "".join(turn.itertext()).strip():
                # It's an empty turn. Check for events:
                for e in turn.findall(".//Event"):
                    results.append(
                        {
                            "xmin": turn_start,
                            "xmax": turn_end,
                            "speaker": speakers[0] if speakers else "nn",
                            "content": f"[{e.get('desc')}]",
                        }
                    )
                continue
            if whos := list(turn.findall(".//Who")):
                frags = self.fragment_whos(turn)
                frags = [i for i in frags if "<Who" in i]

                for frag in frags:
                    frag = etree.fromstring(f"<frag>{frag}</frag>")
                    contents = ""
                    for i in frag.iter():
                        if i.tag == "Event":
                            contents += f" [{i.get('desc')}] {i.text if i.text else ''} {i.tail if i.tail else ''}"
                        else:
                            contents += f" {i.text} {i.tail}".replace("None", "")
                    contents = contents.strip()
                    2 + 2
                    nb = int(frag.find(".//Who").get("nb"))
                    speaker = speakers[nb - 1]
                    results.append(
                        {
                            "xmin": turn_start,
                            "xmax": turn_end,
                            "speaker": speaker,
                            "content": contents,
                        }
                    )
            else:
                start = turn_start
                end = start
                segments = []
                current = None
                for s in turn.iter():
                    if s.tag == "Turn":
                        continue
                    if s.tag == "Sync":
                        if current:
                            current["content"] = contents.strip()
                            current["xmax"] = float(s.get("time"))
                            segments.append(current)
                        contents = f" {s.text} {s.tail}".replace("None", "")
                        start = float(s.get("time"))
                    elif s.tag == "Event":
                        contents += (
                            f" [{s.get('desc')}] {s.text} {s.tail}".strip().replace(
                                "None", ""
                            )
                        )
                    else:
                        1 / 0
                    current = {
                        "xmin": start,
                        "xmax": end,
                        "speaker": speakers[0],
                        "content": contents.strip(),
                    }
                current["xmax"] = turn_end
                if current["content"].strip():
                    segments.append(current)
                else:
                    2 + 2
                results.extend(segments)
        results = sorted(results, key=lambda d: d["xmin"])
        for i, r in enumerate(results):
            text = r["content"].replace("\n", " ")
            while "  " in text:
                text = text.replace("  ", " ")
            results[i]["content"] = text
        return results

    def postprocess_dump(self):
        results = self.contents_dump
        for i in results:
            Segment(**i)
        speakers = set(d["speaker"] for d in results)
        new_results = dict()
        for i in results:
            new_results[i["speaker"]] = new_results.get(i["speaker"], []) + [i]
        if "nn" in new_results:
            self.nn = new_results["nn"]
        else:
            self.nn = []
        # return new_results
        old_speakers = list(new_results.keys())
        for o in old_speakers:
            new_results[self.speaker_table.get(o, o)] = sorted(
                new_results[o], key=lambda d: float(d["xmin"])
            )
            del new_results[o]
        return new_results
