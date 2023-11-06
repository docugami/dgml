def xpath_qname(node) -> str:
    """Get the xpath qname for a node."""
    if node is None:
        return ""

    qname = f"{node.prefix}:{node.tag.split('}')[-1]}"
    parent = node.getparent()
    if parent is not None:
        doppelgangers = [x for x in parent if x.tag == node.tag]
        if len(doppelgangers) > 1:
            idx_of_self = doppelgangers.index(node)
            qname = f"{qname}[{idx_of_self + 1}]"

    return qname


def xpath(node) -> str:
    """Get the xpath for a node."""
    if node is None:
        return ""

    ancestor_chain = node.xpath("ancestor-or-self::*")
    return "/" + "/".join(xpath_qname(x) for x in ancestor_chain)
