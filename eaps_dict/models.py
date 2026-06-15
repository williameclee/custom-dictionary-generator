import json
import itertools
from pathlib import Path
from typing import Optional

templates_dir = Path("templates")
with open(templates_dir / "meaning_templates.json") as f:
    meaning_templates: dict[str, str] = json.load(f)
with open(templates_dir / "term_templates.json") as f:
    term_templates: dict[str, str] = json.load(f)


def populate_list_template(
    items: list[str], list_template: str, item_template: str, replacement_kw: str
) -> str:
    return list_template.replace(
        replacement_kw,
        " ".join([item_template.replace(replacement_kw, t) for t in items]),
    )


class Meaning:
    descriptions: list[str]
    field: Optional[str]
    notes: Optional[str]
    acronyms: set[str]
    synonyms: set[str]
    see_alsos: set[str]

    html_templates: dict[str, str] = meaning_templates

    def __init__(
        self,
        descriptions: list[str] | str,
        field: Optional[str] = None,
        notes: Optional[str] = None,
        acronyms: Optional[list[str] | set[str] | str] = None,
        synonyms: Optional[list[str] | set[str] | str] = None,
        see_alsos: Optional[list[str] | set[str] | str] = None,
    ):
        if isinstance(descriptions, str):
            descriptions = [descriptions]
        self.descriptions = [t.strip() for t in descriptions if t.strip()]

        if field and field.strip():
            self.field = field.strip()
        else:
            self.field = None

        if notes and notes.strip():
            self.notes = notes.strip()
        else:
            self.notes = None

        if acronyms:
            if isinstance(acronyms, str):
                acronyms = acronyms.split(";")
            self.acronyms = set([t.strip() for t in acronyms if t.strip()])
        else:
            self.acronyms = set()

        if synonyms:
            if isinstance(synonyms, str):
                synonyms = synonyms.split(";")
            self.synonyms = set([t.strip() for t in synonyms if t.strip()])
        else:
            self.synonyms = set()

        if see_alsos:
            if isinstance(see_alsos, str):
                see_alsos = see_alsos.split(";")
            self.see_alsos = set([t.strip() for t in see_alsos if t.strip()])
        else:
            self.see_alsos = set()

    @classmethod
    def from_dict(cls, d: dict, is_translation: bool = False):
        if is_translation:
            descriptions = d["translation"]
            # more_descriptions = d.get("translation_synonyms", [])
            # descriptions = itertools.chain.from_iterable(
            #     [descriptions, more_descriptions]
            # )
        else:
            descriptions = d["description"]

        return Meaning(
            descriptions=descriptions,
            field=d.get("field", None),
            notes=d.get("notes", None),
            acronyms=d.get("acronyms", None),
            synonyms=d.get("synonyms", None),
            see_alsos=d.get("see_alsos", None),
        )

    def gen_html(
        self,
        lang: str = "",
        trans_lang: str = "",
    ) -> str:

        xml = self.html_templates["meaning"]

        if self.field:
            field_txt = self.html_templates["field"].replace(r"{FIELD}", self.field)
            xml = xml.replace(r"{FIELD}", field_txt)
        else:
            xml = xml.replace(r"{FIELD}", "")

        if self.notes:
            notes_txt = self.html_templates["notes"].replace(r"{NOTES}", self.notes)
            xml = xml.replace(r"{NOTES}", notes_txt)
        else:
            xml = xml.replace(r"{NOTES}", "")

        for field, items in [
            ("description", self.descriptions),
            ("acronym", sorted(list(self.acronyms))),
            ("synonym", sorted(list(self.synonyms))),
            ("see_also", sorted(list(self.see_alsos))),
        ]:
            rep_kw = f"{{{field.upper()}}}"
            if items:
                xml = xml.replace(
                    rep_kw,
                    populate_list_template(
                        items,
                        self.html_templates[f"{field.lower()}-container"],
                        self.html_templates[field.lower()],
                        rep_kw,
                    ),
                )
            else:
                xml = xml.replace(rep_kw, "")

        xml = xml.replace(r"{LANG}", lang)
        xml = xml.replace(r"{TRANS_LANG}", trans_lang)
        return xml


class Term:
    name: str
    meanings: list[Meaning]
    aliases: list[str]

    xml_template = term_templates

    def __init__(
        self,
        name: str,
        meanings: list[Meaning] | Meaning,
        aliases: Optional[list[str]] = None,
    ):
        self.name = name.strip()
        if isinstance(meanings, Meaning):
            meanings = [meanings]
        self.meanings = meanings

        if aliases:
            if isinstance(aliases, str):
                aliases = aliases.split(";")
            self.aliases = [t.strip() for t in aliases if t.strip()]
        else:
            self.aliases = []

    @property
    def acronyms(self):
        return list(itertools.chain.from_iterable([m.acronyms for m in self.meanings]))

    def gen_xml(
        self, lang: str = "", trans_lang: str = "", source_name: str = ""
    ) -> str:
        val = self.xml_template["val"]
        val = val.replace("{VAL}", self.name)

        for acr in self.acronyms:
            acr_xml = (
                self.xml_template["alt_val"]
                .replace("{ALT_VAL}", acr)
                .replace("{VAL}", self.name)
            )
            val += f"\n\t{acr_xml}"

        for alias in self.aliases:
            alias_xml = (
                self.xml_template["alias_val"]
                .replace("{ALIAS_VAL}", alias)
                .replace("{VAL}", self.name)
            )
            val += f"\n\t{alias_xml}"

        # Build entry
        xml = self.xml_template["term"]
        xml = xml.replace("{VAL}", val)
        xml = xml.replace("{ID}", self.name)
        xml = xml.replace("{TITLE}", self.name)
        xml = xml.replace("{SOURCE}", source_name)
        xml = xml.replace("{H1}", self.name)

        if len(self.meanings) == 1:
            xml = xml.replace(
                "{MEANING}", self.meanings[0].gen_html(lang=lang, trans_lang=trans_lang)
            )
        else:
            xml = xml.replace(
                "{MEANING}",
                populate_list_template(
                    [
                        m.gen_html(lang=lang, trans_lang=trans_lang)
                        for m in self.meanings
                    ],
                    self.xml_template["meaning-list"],
                    self.xml_template["meaning"],
                    "{MEANING}",
                ),
            )

        return xml
