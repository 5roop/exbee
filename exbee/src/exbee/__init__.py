from exbee.exb_parser import EXB
from exbee.trs_parser import TRS

__version__ = "2025.12.30"


def main() -> None:
    trs = TRS("/home/peter/exbee/exbee/tests/ROG-Dia-GSO-P0005-std.trs")
    for i in trs.contents_dump:
        print(i)
