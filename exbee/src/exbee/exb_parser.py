from pathlib import Path
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from loguru import logger
from typing import Self


class EXB:
    def __init__(self, file: Path | str):
        self.path = Path(file)
        self.doc = etree.fromstring(Path(file).read_bytes())
        self.timeline = self.get_timeline()
        self.speakers = self.find_speakers_from_tier_attrib_speaker()

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
        for attribute in ["AutoSave", "Dialect", "Accent", "Check", "Scope"]:
            logger.trace(f"Removing redundant metadata: {attribute}")
            for i in self.doc.findall(
                f'.//ud-information[@attribute-name="{attribute}"]'
            ):
                i.getparent().remove(i)
        logger.trace("Removing tier-format elements")
        for i in self.doc.findall(".//tier-format"):
            i.getparent().remove(i)

    def save(self, file: str | Path) -> None:
        """Saves the doc with Unicode formatting with pretty
        indenting.

        :param str | Path file: Path into which the result will be saved.
        """
        self.remove_duplicated_tlis()

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
        previous = None
        for tli in self.doc.findall(".//tli"):
            if tli.attrib == previous:
                tli.getparent().remove(tli)
            else:
                previous = tli.attrib
        self.update_timeline()

    def copy(self) -> Self:
        """Returns a deep copy of the EXB instance

        :return EXB: Copied instance
        """
        import copy

        return copy.deepcopy(self)
