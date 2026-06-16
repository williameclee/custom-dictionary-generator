from pathlib import Path
import pandas as pd

from typing import Optional


def remove_html_tags(txt: str):
    txt = txt.replace("<em>", "").replace("</em>", "")
    return txt


def split_entry_by(df, sort: bool = True) -> pd.DataFrame:
    df["translation"] = df["translation"].apply(
        lambda x: x.split("; ") if x.count("{") > 1 else x
    )
    df = df.explode("translation")
    df["notes"] = df["translation"].str.extract(r"\{([^}]+)\}")
    df["notes"] = df["notes"].fillna("")
    df["translation"] = df["translation"].str.extract(r"^([^{]+)")
    if sort:
        df = df.sort_values(by=["term", "translation"], key=lambda col: col.str.lower())
    return df


def main(
    csv_path: Path | str,
    output_path: Optional[Path | str] = None,
    overwrite: bool = True,
):
    df = pd.read_csv(csv_path, delimiter="\t")
    df["term"] = df["term"].apply(remove_html_tags)
    df = split_entry_by(df)
    print(df.head())
    print(df.tail())

    if output_path or overwrite:
        if not output_path and overwrite:
            output_path = csv_path
        elif not output_path:
            raise ValueError("Output path not provided")
        df.to_csv(output_path, index=False, sep="\t")


if __name__ == "__main__":
    csv_path = Path("data") / "naer-地質學.csv"
    main(csv_path, output_path=Path("data")/"naer-地質學_cleaned.csv")
