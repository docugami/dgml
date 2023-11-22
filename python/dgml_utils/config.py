from enum import Enum


TABLE_NAME = "{http://www.w3.org/1999/xhtml}table"
STRUCTURE_KEY = "structure"
STYLE_KEY = "style"

DEFAULT_MIN_TEXT_LENGTH = 8  # Default min string length threshold for determining small chunks
DEFAULT_MAX_TEXT_LENGTH = 1024 * 8  # Default max string length cap on returned chunks

DEFAULT_SUBCHUNK_TABLES = False

DEFAULT_TABLE_AS_TEXT_FORMAT = "grid"  # should be a valid format for the tabulate library
DEFAULT_TABLE_AS_TEXT_CELL_MAX_WIDTH = 64

DEFAULT_WHITESPACE_NORMALIZE_TEXT = True
DEFAULT_INCLUDE_XML_TAGS = False

DEFAULT_PARENT_HIERARCHY_LEVELS = 0
DEFAULT_SKIP_TAGS = ["chunk"]  # chunks that are skipped in the parent hierarchy and also not included inline in XML


class HierarchyMode(Enum):
    Structure = 1
    Window = 2


DEFAULT_HIERARCHY_MODE = HierarchyMode.Window

NAMESPACES = {
    "docset": "http://www.docugami.com/2021/dgml/TaqiTest20231103/NDA",
    "addedChunks": "http://www.docugami.com/2021/dgml/TaqiTest20231103/NDA/addedChunks",
    "dg": "http://www.docugami.com/2021/dgml",
    "dgc": "http://www.docugami.com/2021/dgml/docugami/contracts",
    "dgm": "http://www.docugami.com/2021/dgml/docugami/medical",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "cp": "http://classifyprocess.com/2018/07/",
}
