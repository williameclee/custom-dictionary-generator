from pathlib import Path
from .models import Term


def generate_dictionary_xml(
    terms: list[Term],
    templates_dir: Path | str,
    is_translation: bool = False,
    source_name: str | None = None,
) -> str:
    """
    Unified dictionary XML generator.
    Different behaviors are driven by is_translation and template files.
    """
    templates_dir = Path(templates_dir)
    dict_temp_path = templates_dir / "dictionary_template.xml"

    # Choose template file and default source name based on is_translation
    if is_translation:
        if source_name is None:
            source_name = "國家教育研究院"
    else:
        if source_name is None:
            source_name = "NOAA's National Weather Service"

    with open(dict_temp_path, "r", encoding="utf-8") as f:
        dict_template = f.read()

    entries_xml = []

    for term in terms:
        entry_text_str = term.gen_xml(
            trans_lang="chn" if is_translation else "", source_name=source_name
        )

        entries_xml.append(entry_text_str)

    entries_content = "\n".join(entries_xml)
    return dict_template.replace("[ENTRIES]", entries_content)


def generate_nws_xml(
    entries: list[Term],
    templates_dir: Path | str,
    source_name: str = "NOAA's National Weather Service",
) -> str:
    """
    Generates the XML string for the NWS glossary dictionary.
    Wrapper function for backward compatibility.
    """
    return generate_dictionary_xml(
        terms=entries,
        templates_dir=templates_dir,
        is_translation=False,
        source_name=source_name,
    )


def generate_naer_xml(
    entries: list[Term],
    templates_dir: Path | str,
    source_name: str = "國家教育研究院",
) -> str:
    """
    Generates the XML string for the NAER English-Traditional Chinese translation dictionary.
    Wrapper function for backward compatibility.
    """
    return generate_dictionary_xml(
        terms=entries,
        templates_dir=templates_dir,
        is_translation=True,
        source_name=source_name,
    )
