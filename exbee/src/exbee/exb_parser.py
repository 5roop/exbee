from pathlib import Path
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from loguru import logger


class EXB:
    def __init__(self, file: Path | str):
        self.path = Path(file)
        self.doc = etree.fromstring(Path(file).read_bytes())
        # self.timeline = self.get_timeline()
        # self.speakers = self.find_speakers_from_tier_attrib_speaker()
        self.wavfile_raw = Path(self.doc.find(".//referenced-file").attrib["url"])
        self.wavfile_abs = (
            self.path.absolute().resolve().parent / self.wavfile_raw
        ).absolute()

        # Check if trouble:
        if not self.test_tier_id_unique():
            logger.critical(f"Tiers have non-unique ids! Fix it!")
            from collections import Counter

            c = Counter([i.get("id") for i in self.doc.findall(".//tier")])
            logger.critical(f"Non-unique display names: {[i for i in c if c[i] > 1]}")
        if not self.test_tier_display_name_unique():
            logger.critical(f"Tiers have non-unique display names! Fix it!")
            from collections import Counter

            c = Counter(self.get_tier_names())
            logger.critical(f"Non-unique display names: {[i for i in c if c[i] > 1]}")

    def get_tier_names(self):
        tiers = self.doc.findall(".//tier")
        return [t.attrib.get("display-name", "<NO DISPLAY NAME!>") for t in tiers]

    @property
    def tier_names(self):
        """Get the names of all tiers"""
        return [
            t.attrib.get("display-name", "<NO DISPLAY NAME!>")
            for t in self.doc.findall(".//tier")
        ]

    @property
    def timeline(self):
        """Find all <tli> elements and parse them as a dict with id:float pairs"""
        return {
            i.attrib["id"]: float(i.attrib.get("time"))
            for i in self.doc.findall(".//tli")
            if "time" in i.attrib.keys()
        }

    @property
    def speakers(self):
        """Read all the tiers, except the one named [nn], and extract speakers from the attributes"""
        return list(
            dict.fromkeys(
                [
                    i.attrib.get("speaker")
                    for i in self.doc.findall(".//tier")
                    if i.attrib.get("display-name") != "[nn]"
                ]
            )
        )

    def round_timeline(self, decimals=3) -> None:
        """Round all the timestamps to desired precision"""
        for tli in self.doc.findall(".//tli"):
            tli.set("time", str(round(float(tli.get("time")), decimals)))

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

    def find_speakers_from_tier_display_name(self) -> list[str]:
        """Read all the tiers, except the one named [nn], and extract
        speakers from the attributes. The result is in order of appearance.

        :return list[str]: list of speakers
        """
        speakers = [
            i.attrib.get("display-name").split()[0]
            for i in self.doc.findall(".//tier")
            if i.attrib.get("display-name") != "[nn]"
        ]
        return list(dict.fromkeys(speakers))

    def remove_unused_attributes(self) -> None:
        """Removes redundant elements in EXB:
        * AutoSave ud-information
        * Dialect ud-information
        * Accent ud-information
        * Check ud-information
        * Scope ud-information
        * Tier format
        * Tier format table
        * hidden tier tags

        """
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
        # self.remove_duplicated_tlis()
        self.sort_tlis()
        self.remove_unused_attributes()
        if not Path(file).parent.exists():
            logger.info("Creating parent directory")
            Path(file).parent.mkdir(exist_ok=True, parents=True)
        etree.indent(self.doc)
        Path(file).write_text(
            etree.tostring(
                self.doc,
                encoding="unicode",
                pretty_print=True,
                with_tail=True,
                doctype="""<?xml version="1.0" encoding="utf-8"?>""",
            )
        )
        logger.info(f"EXB saved to {file} and formatted prettily.")

    def sort_tlis(self) -> None:
        tl = self.doc.find(".//common-timeline")
        tl[:] = sorted(tl[:], key=lambda tli: float(tli.attrib.get("time", 0)))

    def remove_duplicated_tlis(self) -> None:
        """Performs exact deduplication on TLI elements in place. If duplicates
        are found, they  will be removed and their references in events will be
        changed to the non-duplicated ones."""

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

    def add_to_timeline(
        self, timestamp_seconds: float, remove_duplicated: bool = True
    ) -> str:
        """Returns the id of tli at timestamp_seconds. If there was one already,
        it will be recycled, else a new one will be created. Time resolution: 1ms

        :param float timestamp_seconds: Time at which to create the tli
        :return str: the id of the tli at timestamp_seconds
        """
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
        if remove_duplicated:
            self.remove_duplicated_tlis()
        self.sort_tlis()
        return proposed_id

    def test_tier_id_unique(self):
        ids = self.doc.xpath(".//tier/@id")
        return len(ids) == len(set(ids))

    def test_tier_display_name_unique(self):
        dispnames = self.doc.xpath(".//tier/@display-name")
        return len(dispnames) == len(set(dispnames))

    def remove_duplicated_tiers(self):
        """Removes tier, if there is another one with the same attributes
        and the same children."""
        seen = {}
        tiers_to_remove = []
        etree.indent(self.doc)
        for tier in self.doc.findall(".//tier"):
            # Get the full XML string of this tier (attributes + children + text)
            tier_xml = etree.tostring(tier, encoding="unicode")

            if tier_xml in seen:
                tiers_to_remove.append(tier)
                logger.warning(
                    f"Removing duplicate tier id='{tier.get('id', '?')}' "
                    f"display-name='{tier.get('display-name', '?')}' — "
                    f"duplicate of id='{seen[tier_xml].get('id', '?')}'"
                )
            else:
                seen[tier_xml] = tier

        for tier in tiers_to_remove:
            tier.getparent().remove(tier)

        logger.info(f"Removed {len(tiers_to_remove)} duplicate tier(s)")
