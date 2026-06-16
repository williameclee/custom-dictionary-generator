import pandas as pd
from pathlib import Path

from .models import Term, Meaning


def clean_split(value: str, delimiter: str = "; ") -> list[str]:
    """Helper to split a string by delimiter, strip whitespace, and filter empty results."""
    if not value:
        return []
    # Normalise different delimiters to the delimiter (e.g. "; ")
    normalised = value.replace("；", delimiter).replace("、", delimiter)
    parts = normalised.split(delimiter)
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
    entry_col: str = "term",
    translation_cols: list[str] | str = "translation",
) -> dict[str, set[str]]:
    """
    Returns a dictionary that contains the mapping from a translation to its corresponding term(s) in the original language.
    """
    if isinstance(translation_cols, str):
        translation_cols = [translation_cols]

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
    sort: bool = False,
    gen_synonyms_from_translation: bool = False,
) -> pd.DataFrame:
    df = pd.read_csv(csv_path, delimiter="\t", dtype=str)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["term"]).fillna("")
    df = df.map(lambda x: x.strip() if isinstance(x, str) else "")

    # Ensure all standard columns are present
    expected_cols = [
        "term",
        "acronyms",
        "description",
        "field",
        "synonyms",
        "see_alsos",
        "aliases",
        "translation",
        "translation_synonyms",
        "notes",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    # Clean up fields into lists
    for col in [
        "acronyms",
        "aliases",
        "synonyms",
        "see_alsos",
        "translation",
        "translation_synonyms",
    ]:
        df[col] = df[col].apply(lambda t: clean_split(t))

    # Merge translation synonyms into translation list
    df["translation"] = df.apply(
        lambda d: unique_ordered(d["translation"] + d["translation_synonyms"]), axis=1
    )

    df = df.drop(columns=["translation_synonyms"])

    # Sort if requested
    if sort:
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
    if gen_synonyms_from_translation and "translation" in df.columns:
        translation_pairs = find_entries_with_same_translation(
            df, "term", "translation"
        )

        def find_synonym(name: str, translations: list[str]) -> list[str]:
            syns = set()
            for t in translations:
                syns.update(translation_pairs.get(t, set()) - {name})
            return sorted(list(syns))

        # Update synonym column by combining with any existing synonyms
        df["synonyms"] = df.apply(
            lambda r: unique_ordered(
                r["synonyms"] + find_synonym(r["term"], r["translation"])
            ),
            axis=1,
        )

    return df


def parse_dictionary_csv(
    csv_paths: list[Path | str] | Path | str,
    is_translation: bool = False,
    sort: bool = False,
    gen_synonyms: bool = False,
) -> list[Term]:
    """
    Unified dictionary parser using pandas.
    Different behaviors are driven by argument flags.
    """
    if isinstance(csv_paths, (str, Path)):
        csv_paths = [csv_paths]

    dfs = []
    for csv_path in csv_paths:
        csv_path = Path(csv_path)
        if not csv_path.exists():
            continue
        df_file = load_and_clean_csv(
            csv_path,
            sort=False,  # Sort after merging
            gen_synonyms_from_translation=gen_synonyms,
        )
        if not df_file.empty:
            dfs.append(df_file)

    if not dfs:
        return []

    # Concatenate all DataFrames
    df = pd.concat(dfs, ignore_index=True)

    # Perform stable sort on merged dataframe if requested
    if sort:
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

    # Group entries by the term column preserving order of appearance in the dataframe
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

    # Construct Term objects
    terms = [
        Term(
            name=name,
            meanings=term_dict[name],
            aliases=unique_ordered(alias_dict.get(name, [])),
        )
        for name in names
    ]
    return terms
