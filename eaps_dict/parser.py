import pandas as pd
from pathlib import Path

from .models import Term, Meaning


def clean_split(value: str, delimiter: str = "; ") -> list[str]:
    """Helper to split a string by delimiter, strip whitespace, and filter empty results."""
    if not value:
        return []
    parts = value.split(delimiter)
    cleaned = []
    for p in parts:
        p_strip = p.strip()
        if p_strip:
            cleaned.append(p_strip)
    return cleaned


def unique_ordered(items: list[str]) -> list[str]:
    """Returns unique items while preserving their original order of appearance."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def find_entries_with_same_translation(
    df: pd.DataFrame,
    entry_col: str = "Entry",
    translation_cols: list[str] | str = ["translation", "translation_synonyms"],
) -> dict[str, set[str]]:
    """
    Returns a dictionary the contains the mapping from a translation to its corresponding term(s) in the original language.
    """
    if isinstance(translation_cols, str):
        translation_cols = [translation_cols]
    assert entry_col in df and (
        all([col in df for col in translation_cols])
    ), f"Either '{entry_col}' or '{translation_cols}' is not a column of the input DataFrame."

    translation_pairs = {}
    for _, row in df.iterrows():
        entry = row[entry_col]
        if not entry:
            continue
        for col in translation_cols:
            translation = row[col]
            if not translation:
                continue
            if isinstance(translation, list):
                for t in translation:
                    if t not in translation_pairs:
                        translation_pairs[t] = set()
                    translation_pairs[t].add(entry)
                continue
            if translation not in translation_pairs:
                translation_pairs[translation] = set()
            translation_pairs[translation].add(entry)
    return translation_pairs


def load_and_clean_csv(
    csv_path: Path | str,
    sort_alphabetically: bool = False,
    gen_synonyms_from_translation: bool = False,
) -> pd.DataFrame:
    df = pd.read_csv(csv_path, delimiter="\t", dtype=str)

    # Basic cleaning
    df.columns = df.columns.str.strip()
    df = df.dropna(subset="term")
    df = df.fillna("")
    df = df.map(lambda x: x.strip() if isinstance(x, str) else "")

    # Clean up columns
    if "acronyms" in df:
        df["acronyms"] = df["acronyms"].apply(lambda t: clean_split(t))
    if "aliases" in df:
        df["aliases"] = df["aliases"].apply(lambda t: clean_split(t))
    if "synonyms" in df:
        df["synonyms"] = df["synonyms"].apply(lambda t: clean_split(t))
    if "see_alsos" in df:
        df["see_alsos"] = df["see_alsos"].apply(lambda t: clean_split(t))
    if "translation" in df:
        df["translation"] = df["translation"].apply(lambda t: clean_split(t))
    if "translation_synonyms" in df:
        df["translation_synonyms"] = df["translation_synonyms"].apply(
            lambda t: clean_split(t)
        )
        if "translation" in df:
            for _, row in df.iterrows():
                row["translation"] += row["translation_synonyms"]
            df = df.drop(columns=["translation_synonyms"])

    # Sort if requested
    if sort_alphabetically:
        sort_cols = []
        if "term" in df.columns:
            sort_cols.append("term")
        if "translation" in df.columns:
            df["translation_aux"] = df["translation"].apply(lambda l: "".join(l))
            sort_cols.append("translation_aux")
        if sort_cols:
            df = df.sort_values(by=sort_cols, kind="stable")
        if "translation_aux" in df:
            df = df.drop(columns=["translation_aux"])

    # Find synonyms if requested
    if gen_synonyms_from_translation and "translation" in df:
        translation_pairs = find_entries_with_same_translation(
            df, "term", "translation"
        )

        def find_synonym(name: str, translations: list[str]) -> list[str]:
            synonyms = set()
            for t in translations:
                synonyms.update(translation_pairs[t] - {name})
            return list(synonyms)

        df["synonyms"] = df.apply(
            lambda r: find_synonym(r["term"], r["translation"]), axis=1
        )

    return df


def parse_dictionary_csv(
    csv_path: Path | str,
    is_translation: bool = False,
    sort_alphabetically: bool = False,
    gen_synonyms_from_translation: bool = False,
) -> list[Term]:
    """
    Unified dictionary parser using pandas.
    Different behaviors are driven by argument flags.
    """
    df = load_and_clean_csv(
        csv_path,
        sort_alphabetically=sort_alphabetically,
        gen_synonyms_from_translation=gen_synonyms_from_translation,
    )

    # Group entries by the first column ('Entry' for both NWS and NAER)
    # preserving order of appearance in the (possibly sorted) dataframe.
    term_dict: dict[str, list[Meaning]] = {}
    alias_dict: dict[str, list[str]] = {}
    names: list[str] = []

    for _, meaning_row in df.iterrows():
        name: str = meaning_row["term"]
        if not name:
            continue

        meaning = Meaning.from_dict(
            meaning_row.to_dict(), is_translation=is_translation
        )
        if name not in term_dict:
            term_dict[name] = []
            names.append(name)
        term_dict[name].append(meaning)

        aliases = meaning_row["aliases"]
        if name not in alias_dict:
            alias_dict[name] = []
        alias_dict[name] += aliases

    terms = [Term(name, term_dict[name], alias_dict.get(name, None)) for name in names]
    return terms


def parse_nws_glossary(csv_path: Path | str) -> list[Term]:
    """Wrapper function to parse NWS glossary for backward compatibility."""
    return parse_dictionary_csv(
        csv_path,
        is_translation=False,
        sort_alphabetically=False,
        gen_synonyms_from_translation=False,
    )


def parse_naer_translations(csv_path: Path | str) -> list[Term]:
    """Wrapper function to parse NAER translations for backward compatibility."""
    return parse_dictionary_csv(
        csv_path,
        is_translation=True,
        sort_alphabetically=True,
        gen_synonyms_from_translation=True,
    )
