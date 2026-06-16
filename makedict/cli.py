import argparse
import sys
from pathlib import Path
import subprocess
import logging
import yaml
from typing import Any

from makedict.parser import parse_dictionary_csv
from makedict.generator import generate_dictionary_xml
from makedict.compiler import compile_dictionary

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_PATHS = {
    "ddk_dir": "/Applications/Utilities/DictionaryDevelopmentKit",
    "dest_dir": "~/Library/Dictionaries",
    "dict_app": "/System/Applications/Dictionary.app/",
}


def reload_dictionary_app():
    """Closes and reopens macOS Dictionary.app to load the new dictionary."""
    logger.info("Reloading Dictionary.app...")
    subprocess.run(
        ["killall", "Dictionary"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        subprocess.run(["open", DEFAULT_PATHS["dict_app"]], check=True)
        logger.info("Dictionary.app reloaded successfully.")
    except Exception as e:
        logger.warning(f"Could not open Dictionary.app: {e}")


def generate_plist_file(
    identifier: str,
    bundle_name: str,
    plist_path: Path,
    templates_dir: Path,
    manufacturer: str = "En-Chi Lee",
    development_region: str = "English",
    version: str = "1.0",
    front_matter_id: str = "front_back_matter",
    copyright: str | None = None,
):
    """Generates the plist configuration file dynamically from a template."""
    plist_temp_path = templates_dir / "plist_template.plist"
    if not plist_temp_path.exists():
        # Fallback inline template if file doesn't exist
        logger.warning(
            f"plist template not found at {plist_temp_path.as_posix()}, using fallback."
        )
        content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>{DEVELOPMENT_REGION}</string>
	<key>CFBundleIdentifier</key>
	<string>{IDENTIFIER}</string>
	<key>CFBundleName</key>
	<string>{BUNDLE_NAME}</string>
	<key>CFBundleShortVersionString</key>
	<string>{VERSION}</string>
	<key>DCSDictionaryManufacturerName</key>
	<string>{MANUFACTURER}</string>
	<key>DCSDictionaryFrontMatterReferenceID</key>
	<string>{FRONT_MATTER_ID}</string>{COPYRIGHT_KEY_VAL}
	<key>DCSDictionaryDefaultPrefs</key>
	<dict>
		<key>pronunciation</key>
		<string>0</string>
		<key>display-column</key>
		<string>1</string>
		<key>display-picture</key>
		<string>1</string>
		<key>version</key>
		<string>1</string>
	</dict>
	<key>DCSDictionaryUseSystemAppearance</key>
	<true/>
</dict>
</plist>
"""
    else:
        with open(plist_temp_path, "r", encoding="utf-8") as f:
            content = f.read()

    copyright_xml = ""
    if copyright:
        copyright_xml = (
            f"\n\t<key>DCSDictionaryCopyright</key>\n\t<string>{copyright}</string>"
        )

    content = content.replace("{DEVELOPMENT_REGION}", development_region)
    content = content.replace("{IDENTIFIER}", identifier)
    content = content.replace("{BUNDLE_NAME}", bundle_name)
    content = content.replace("{VERSION}", version)
    content = content.replace("{MANUFACTURER}", manufacturer)
    content = content.replace("{FRONT_MATTER_ID}", front_matter_id)
    content = content.replace("{COPYRIGHT_KEY_VAL}", copyright_xml)

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    with open(plist_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Generated plist file at '{plist_path.as_posix()}'")


def run_pipeline(
    dict_id: str,
    dict_name: str,
    input_csvs: list[Path | str],
    css_path: Path | str,
    templates_dir: Path | str,
    is_translation: bool,
    sort_alphabetically: bool,
    generate_synonyms: bool,
    lang: str = "en",
    trans_lang: str = "en",
    source_name: str | None = None,
    plist_config: dict[str, Any] | None = None,
    ddk_dir: Path | str = Path(DEFAULT_PATHS["ddk_dir"]),
    dest_dir: Path | str = Path(DEFAULT_PATHS["dest_dir"]),
    no_compile: bool = False,
) -> bool:
    """
    Generalized dictionary pipeline.
    All arguments are explicitly passed for observability and reusability.
    """
    dict_id = dict_id.strip()
    dict_name = dict_name.strip()
    input_csvs = [Path(p) for p in input_csvs]
    css_path = Path(css_path)
    templates_dir = Path(templates_dir)
    ddk_dir = Path(ddk_dir)
    dest_dir = Path(dest_dir)

    logger.info(f"Starting pipeline for '{dict_name}' (ID: {dict_id})...")

    # Verify input CSVs exist
    valid_csvs = []
    for csv_path in input_csvs:
        if csv_path.exists():  # type: ignore
            valid_csvs.append(csv_path)
        else:
            logger.warning(f"Input CSV not found: '{csv_path.as_posix()}'")  # type: ignore

    if not valid_csvs:
        logger.error("No valid input CSV files specified.")
        return False

    # 1. Parse CSV data
    logger.info(f"Parsing input files: {[p.name for p in valid_csvs]}...")
    entries = parse_dictionary_csv(
        csv_paths=valid_csvs,
        is_translation=is_translation,
        sort=sort_alphabetically,
        gen_synonyms=generate_synonyms,
    )
    logger.info(f"Parsed {len(entries)} grouped dictionary entries.")

    # 2. Generate XML source
    xml_content = generate_dictionary_xml(
        entries=entries,
        templates_dir=templates_dir,
        source_name=source_name,
        lang=lang,
        trans_lang=trans_lang,
    )

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    xml_path = outputs_dir / f"{dict_id}.xml"
    xml_path.write_text(xml_content, encoding="utf-8")
    logger.info(f"Generated XML file '{xml_path.as_posix()}'")

    # 3. Generate plist file
    plist_path = outputs_dir / f"{dict_id}.plist"
    plist_config = plist_config or {}
    generate_plist_file(
        identifier=plist_config.get("identifier", f"com.enchilee.dictionary.{dict_id}"),
        bundle_name=plist_config.get("bundle_name", dict_name),
        plist_path=plist_path,
        templates_dir=templates_dir,
        manufacturer=plist_config.get("manufacturer", "En-Chi Lee"),
        development_region=plist_config.get("development_region", "English"),
        version=plist_config.get("version", "1.0"),
        front_matter_id=plist_config.get("front_matter_id", "front_back_matter"),
        copyright=plist_config.get("copyright"),
    )

    # 4. Compile if requested
    if no_compile:
        logger.info("Compilation disabled by user.")
        return True

    compiled = compile_dictionary(
        dict_name=dict_name,
        xml_path=xml_path,
        css_path=css_path,
        plist_path=plist_path,
        ddk_dir=ddk_dir,
        dest_dir=dest_dir,
    )
    return compiled


def main():
    parser = argparse.ArgumentParser(
        description="Compile dictionaries dynamically using configuration files or CLI overrides."
    )
    parser.add_argument(
        "--config",
        help="Path to the YAML configuration file (e.g. configs/nws-glossary.yaml)",
    )
    parser.add_argument(
        "--id",
        help="Dictionary ID (filename base and identifier prefix)",
    )
    parser.add_argument(
        "--name",
        help="Dictionary display name",
    )
    parser.add_argument(
        "--lang",
        help="Primary terms language (default: en)",
    )
    parser.add_argument(
        "--trans-lang",
        help="Translation language (default: en)",
    )
    parser.add_argument(
        "--source",
        help="Dictionary credit source name",
    )
    parser.add_argument(
        "--is-translation",
        action="store_true",
        default=None,
        help="Specify that this is a translation dictionary",
    )
    parser.add_argument(
        "--no-is-translation",
        action="store_false",
        dest="is_translation",
        help="Specify that this is NOT a translation dictionary",
    )
    parser.add_argument(
        "--sort",
        action="store_true",
        default=None,
        dest="sort_alphabetically",
        help="Sort entries alphabetically",
    )
    parser.add_argument(
        "--no-sort",
        action="store_false",
        dest="sort_alphabetically",
        help="Do not sort entries alphabetically",
    )
    parser.add_argument(
        "--generate-synonyms",
        action="store_true",
        default=None,
        dest="generate_synonyms",
        help="Generate English synonyms from shared translations",
    )
    parser.add_argument(
        "--no-generate-synonyms",
        action="store_false",
        dest="generate_synonyms",
        help="Do not generate English synonyms from shared translations",
    )
    parser.add_argument(
        "--input-csvs",
        nargs="+",
        help="Input CSV data file paths",
    )
    parser.add_argument(
        "--css",
        help="Path to CSS file stylesheet",
    )
    parser.add_argument(
        "--templates-dir",
        default="templates",
        help="Directory containing XML/plist templates (default: templates)",
    )
    parser.add_argument(
        "--ddk-dir",
        default=DEFAULT_PATHS["ddk_dir"],
        help=f"Path to macOS Dictionary Development Kit (default: {DEFAULT_PATHS['ddk_dir']})",
    )
    parser.add_argument(
        "--dest-dir",
        default=DEFAULT_PATHS["dest_dir"],
        help=f"Path where compiled dictionaries are installed (default: {DEFAULT_PATHS['dest_dir']})",
    )
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Generate XML and plist source files without compiling",
    )
    parser.add_argument(
        "--reload-app",
        action="store_true",
        help="Automatically reload Dictionary.app on successful compilation",
    )

    args = parser.parse_args()

    # Base configuration loaded from file
    config_dict = {}
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: '{config_path.as_posix()}'")
            sys.exit(1)
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}

    # Merge configuration with CLI arguments (CLI overrides config)
    dict_cfg = config_dict.get("dictionary", {})
    assets_cfg = config_dict.get("assets", {})
    plist_cfg = config_dict.get("plist", {})

    dict_id = args.id or dict_cfg.get("id")
    dict_name = args.name or dict_cfg.get("name")
    lang = args.lang or dict_cfg.get("lang", "en")
    trans_lang = args.trans_lang or dict_cfg.get("trans_lang", "en")
    source_name = args.source or dict_cfg.get("source")

    is_translation = args.is_translation
    if is_translation is None:
        is_translation = dict_cfg.get("is_translation", False)

    sort_alphabetically = args.sort_alphabetically
    if sort_alphabetically is None:
        sort_alphabetically = dict_cfg.get("sort_alphabetically", False)

    generate_synonyms = args.generate_synonyms
    if generate_synonyms is None:
        generate_synonyms = dict_cfg.get("generate_synonyms", False)

    input_csvs = args.input_csvs
    if not input_csvs:
        input_csvs = config_dict.get("input_files", [])

    css_path = args.css or assets_cfg.get("css")

    # Assert required fields exist
    if not dict_id:
        logger.error(
            "Error: Dictionary ID is required (specify in config or via --id)."
        )
        sys.exit(1)
    if not dict_name:
        logger.error(
            "Error: Dictionary Name is required (specify in config or via --name)."
        )
        sys.exit(1)
    if not input_csvs:
        logger.error(
            "Error: Input CSV(s) are required (specify in config or via --input-csvs)."
        )
        sys.exit(1)
    if not css_path:
        logger.error(
            "Error: CSS stylesheet path is required (specify in config or via --css)."
        )
        sys.exit(1)

    success = run_pipeline(
        dict_id=dict_id,
        dict_name=dict_name,
        input_csvs=input_csvs,
        css_path=css_path,
        templates_dir=args.templates_dir,
        is_translation=is_translation,
        sort_alphabetically=sort_alphabetically,
        generate_synonyms=generate_synonyms,
        lang=lang,
        trans_lang=trans_lang,
        source_name=source_name,
        plist_config=plist_cfg,
        ddk_dir=args.ddk_dir,
        dest_dir=args.dest_dir,
        no_compile=args.no_compile,
    )

    if success and not args.no_compile and args.reload_app:
        reload_dictionary_app()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
