from pathlib import Path
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from loguru import logger


class EXB:
    def __init__(self, file: Path | str):
        self.path = Path(file)
        self.doc = etree.fromstring(Path(file).read_bytes())
        self.timeline = self.get_timeline()
        self.speakers = self.find_speakers_from_tier_attrib_speaker()
        self.wavfile_raw = Path(self.doc.find(".//referenced-file").attrib["url"])
        self.wavfile_abs = (
            self.path.absolute().resolve().parent / self.wavfile_raw
        ).absolute()

    def get_tier_names(self):
        tiers = self.doc.findall(".//tier")
        return [t.attrib.get("display-name", "<NO DISPLAY NAME!>") for t in tiers]

    def get_timeline(self):
        """Find all <tli> element and parse them as dict
        with id:float pairs

        :return dict[str, float]: timeline dictionary, keys are IDS, values are times
        """
        return {
            i.attrib["id"]: float(i.attrib["time"]) for i in self.doc.findall(".//tli")
        }

    def update_timeline(self) -> None:
        self.timeline = self.get_timeline()

    def find_speakers_from_tier_attrib_speaker(self) -> list[str]:
        """Read all the tiers, except the one named [nn], and extract
        speakers from the attributes. The result is in order of appearance.

        :return list[str]: list of speakers
        """
        speakers = [
            i.attrib.get("speaker")
            for i in self.doc.findall(".//tier")
            if i.attrib.get("display-name") != "[nn]"
        ]
        return list(dict.fromkeys(speakers))

    def remove_unused_attributes(self) -> None:
        for attribute in [
            "AutoSave",
            "Dialect",
            "Accent",
            "Check",
            "Scope",
        ]:
            logger.trace(f"Removing redundant metadata: {attribute}")
            for i in self.doc.findall(
                f'.//ud-information[@attribute-name="{attribute}"]'
            ):
                i.getparent().remove(i)
        logger.trace("Removing tier-format elements")
        for i in self.doc.findall(".//tier-format"):
            i.getparent().remove(i)
        for i in self.doc.findall(".//tierformat-table"):
            i.getparent().remove(i)
        for attribute in [
            "exmaralda:hidden",
        ]:
            logger.trace(f"Removing redundant metadata: {attribute}")
            for i in self.doc.findall(
                f'.//ud-information[@attribute-name="{attribute}"]'
            ):
                parent = i.getparent()
                parent.remove(i)
                parent.getparent().remove(parent)

    def save(self, file: str | Path) -> None:
        """Saves the doc with Unicode formatting with pretty
        indenting.

        :param str | Path file: Path into which the result will be saved.
        """
        self.remove_duplicated_tlis()
        self.sort_tlis()
        self.remove_unused_attributes()

        Path(file).parent.mkdir(exist_ok=True, parents=True)
        Path(file).write_text(
            etree.tostring(self.doc, encoding="unicode", pretty_print=True),
            encoding="utf8",
        )
        import subprocess

        subprocess.run(
            ["xmllint", "--format", file, "--encode", "utf-8", "--output", file],
            check=True,
            capture_output=True,
            # text=True,
        )
        logger.info(f"EXB saved to {file} and formatted prettily.")

    def sort_tlis(self) -> None:
        tl = self.doc.find(".//common-timeline")
        tl[:] = sorted(tl[:], key=lambda tli: float(tli.attrib.get("time", 0)))
        self.update_timeline()

    def remove_duplicated_tlis(self) -> None:
        """Performs exact deduplication on TLI elements in place."""
        self.sort_tlis()
        previous = dict(id=None, time=None)
        for tli in self.doc.findall(".//tli"):
            if tli.attrib["time"] == previous["time"]:
                id = tli.attrib["id"]
                for what in ["start", "stop"]:
                    for event in self.doc.findall(f".//event[@{what}='{id}']"):
                        event.attrib[what] = previous["id"]
                logger.trace(
                    f"Removing tli with id {tli.attrib['id']} and time {tli.attrib['time']}, duplicate of {previous['id']} at {previous['time']}"
                )
                tli.getparent().remove(tli)
            else:
                previous = tli.attrib
        self.update_timeline()

    def copy(self):
        """Returns a deep copy of the EXB instance

        :return EXB: Copied instance
        """
        import copy

        return copy.deepcopy(self)

    def add_trailing_spaces(self):
        """Strip all events with text and then append a trailing space."""
        for event in self.doc.findall(".//event"):
            if event.text:
                event.text = event.text.strip() + " "

    @staticmethod
    def add_trailing_spaces_to_tier(tier):
        """Within the tier, strip all events with text and then append a trailing space."""
        for event in tier.findall(".//event"):
            if event.text:
                event.text = event.text.strip() + " "

    def add_to_timeline(self, timestamp_seconds: float) -> str:
        # self.update_timeline()
        timeline = self.timeline

        if round(timestamp_seconds, 3) in [round(i, 3) for i in timeline.values()]:
            for id, time in timeline.items():
                if round(timestamp_seconds, 3) == round(time, 3):
                    return id
        L = len(timeline) + 1
        while True:
            proposed_id = f"T{L}"
            if proposed_id in self.timeline.keys():
                L += 1
            else:
                break
        tli = etree.Element("tli")
        tli.attrib["id"] = proposed_id
        tli.attrib["time"] = str(round(timestamp_seconds, 3))
        self.doc.find(".//common-timeline").append(tli)
        self.remove_duplicated_tlis()
        return proposed_id
