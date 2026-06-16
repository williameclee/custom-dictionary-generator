import json
from pathlib import Path
from .models import Term, Meaning


def generate_dictionary_xml(
    entries: list[Term],
    templates_dir: Path | str,
    source_name: str | None = None,
    lang: str = "en",
    trans_lang: str = "en",
) -> str:
    """
    Unified dictionary XML generator.
    Loads templates dynamically, configures Term/Meaning classes, and calls term.gen_xml().
    """
    templates_dir = Path(templates_dir)
    dict_temp_path = templates_dir / "dictionary_template.xml"
    term_temps_path = templates_dir / "term_templates.json"
    meaning_temps_path = templates_dir / "meaning_templates.json"

    # Reload templates dynamically from user-specified templates directory
    with open(term_temps_path, "r", encoding="utf-8") as f:
        Term.xml_template = json.load(f)
    with open(meaning_temps_path, "r", encoding="utf-8") as f:
        Meaning.html_templates = json.load(f)

    with open(dict_temp_path, "r", encoding="utf-8") as f:
        dict_template = f.read()

    # Map the translation language to class placeholders
    # In NAER, the translation class is "chn" if trans_lang contains "zh" or "chn"
    trans_lang_cls = (
        "chn" if "zh" in trans_lang.lower() or trans_lang.lower() == "chn" else ""
    )

    entries_xml = []
    for term in entries:
        # Generate entry XML using class method
        entry_text = term.gen_xml(
            lang=lang,
            trans_lang=trans_lang_cls,
            source_name=source_name,
        )
        entries_xml.append(entry_text)

    entries_content = "\n".join(entries_xml)
    return dict_template.replace("[ENTRIES]", entries_content)
