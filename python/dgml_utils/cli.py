import sys
import typer

from pathlib import Path

app = typer.Typer(
    help="Command line utility for dgml_utils",
    no_args_is_help=True,
)


@app.command()
def prettyprint(
    dgml: Path = typer.Argument(
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="DGML file to pretty print",
    ),
    include_xml_tags: bool = False,
):
    """
    Pretty prints the given DGML
    """

    from dgml_utils.segmentation import get_chunks_str

    # Read contents of dgml file
    with open(dgml, "r", encoding="utf-8") as file:
        dgml_str = file.read()

    chunks = get_chunks_str(
        dgml=dgml_str,
        include_xml_tags=include_xml_tags,
        parent_hierarchy_levels=0,
    )

    output = "\n".join([chunk.text for chunk in chunks])

    typer.echo(output)


if __name__ == "__main__":
    if sys.gettrace():
        # This code will only run if a debugger is attached

        test_file = Path(__file__).parent / "../tests/test_data/article/Jane Doe.xml"
        prettyprint(dgml=test_file, include_xml_tags=False)
