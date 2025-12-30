from lxml import etree
import json


from pathlib import Path

xml_data = Path("/home/peter/exbee/exbee/tests/ROG-Dia-GSO-P0005-std.trs").read_bytes()

doc = etree.fromstring(xml_data)


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


def parse_into_contents(doc: etree._Element):
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
            frags = fragment_whos(turn)
            frags = [i for i in frags if "<Who" in i]

            for frag in frags:
                frag = etree.fromstring(f"<frag>{frag}</frag>")
                contents = ""
                for i in frag.iter():
                    if i.tag == "Event":
                        contents += f" [{i.get('desc')}]"
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
                    contents += f" [{s.get('desc')}] {s.text} {s.tail}".strip().replace(
                        "None", ""
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
    return results
    2 + 2
    for i in results:
        print(i)
    2 + 2


parse_into_contents(doc)
