TABLE_NAME = "{http://www.w3.org/1999/xhtml}table"
STRUCTURE_KEY = "structure"

DEFAULT_MIN_CHUNK_LENGTH = 8  # Default length threshold for determining small chunks
DEFAULT_SUBCHUNK_TABLES = False
DEFAULT_TABLE_FORMAT_AS_TEXT = "grid"  # should be a valid format for the tabulate library
DEFAULT_WHITESPACE_NORMALIZE_TEXT = True
DEFAULT_INCLUDE_XML_TAGS = False
DEFAULT_XML_HIERARCHY_LEVELS = 0
DEFAULT_SKIP_XML_TAGS = ["chunk"]  # chunks that are skipped in the parent hierarchy and also not included inline in XML
DEFAULT_MAX_TEXT_LENGTH = 1024

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
