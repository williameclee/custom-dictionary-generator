import json
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_templates():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Dictionary template
        (tmp_path / "dictionary_template.xml").write_text(
            "<d:dictionary>[ENTRIES]</d:dictionary>", encoding="utf-8"
        )

        # Term templates
        term_data = {
            "term": '<d:entry id="{ID}" d:title="{TITLE}">\n\t{VAL}\n\t<div class="container">\n\t\t<h1>{H1}<span class="source">{SOURCE}</span></h1>\n\t\t<div class="body">{MEANING}</div>\n\t</div>\n</d:entry>',
            "meaning-list": '<ol class="meanings">{MEANING}</ol>',
            "meaning": "<li>{MEANING}</li>",
            "val": '<d:index d:value="{VAL}"/>',
            "alt_val": '<d:index d:value="{ALT_VAL}" d:title="{VAL} ({ALT_VAL})"/>',
            "alias_val": '<d:index d:value="{ALIAS_VAL}" d:title="{VAL}"/>',
        }
        (tmp_path / "term_templates.json").write_text(
            json.dumps(term_data), encoding="utf-8"
        )

        # Meaning templates
        meaning_data = {
            "meaning": "<p>{FIELD}{DESCRIPTION}{NOTES}</p>{ACRONYM}{SYNONYM}{SEE_ALSO}",
            "field": '<span class="field {TRANS_LANG}">{FIELD}</span>',
            "description-container": '<span class="description-container {TRANS_LANG}">{DESCRIPTION}</span>',
            "description": '<span class="description {TRANS_LANG}">{DESCRIPTION}</span>',
            "notes": '<span class="notes {TRANS_LANG}">{NOTES}</span>',
            "acronym-container": '\n<p class="acronym-container {TRANS_LANG}">{ACRONYM}</p>',
            "acronym": '<span class="acronym {LANG}">{ACRONYM}</span>',
            "synonym-container": '\n<p class="synonym-container {TRANS_LANG}">{SYNONYM}</p>',
            "synonym": '<span class="synonym {LANG}">{SYNONYM}</span>',
            "see_also-container": '\n<p class="see_also-container {TRANS_LANG}">{SEE_ALSO}</p>',
            "see_also": '<span class="see_also {LANG}">{SEE_ALSO}</span>',
        }
        (tmp_path / "meaning_templates.json").write_text(
            json.dumps(meaning_data), encoding="utf-8"
        )

        # Translation template (same as term for simplicity in tests)
        (tmp_path / "translation_template.xml").write_text(
            term_data["term"], encoding="utf-8"
        )
        (tmp_path / "entry_template.xml").write_text(
            term_data["term"], encoding="utf-8"
        )

        yield tmp_path
