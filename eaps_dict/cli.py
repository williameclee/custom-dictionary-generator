import argparse
import sys
from pathlib import Path
import subprocess
from eaps_dict.parser import parse_nws_glossary, parse_naer_translations
from eaps_dict.generator import generate_nws_xml, generate_naer_xml
from eaps_dict.compiler import compile_dictionary

import logging

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
    # Kill the app if running (ignore errors if not running)
    subprocess.run(
        ["killall", "Dictionary"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    # Open the app
    try:
        subprocess.run(["open", DEFAULT_PATHS["dict_app"]], check=True)
        logger.info("Dictionary.app reloaded successfully.")
    except Exception as e:
        logger.warning(f"Could not open Dictionary.app: {e}")


def run_nws_pipeline(
    nws_csv: Path | str,
    templates_dir: Path | str,
    ddk_dir: Path | str = Path(DEFAULT_PATHS["ddk_dir"]),
    dest_dir: Path | str = Path(DEFAULT_PATHS["dest_dir"]),
    no_compile: bool = False,
) -> bool:
    nws_csv = Path(nws_csv)
    templates_dir = Path(templates_dir)
    ddk_dir = Path(ddk_dir)
    dest_dir = Path(dest_dir)

    logger.info(f"Starting NWS Glossary pipeline using '{nws_csv.as_posix()}'...")
    if not nws_csv.exists():
        logger.error(f"NWS glossary CSV not found at '{nws_csv.as_posix()}'")
        return False

    entries = parse_nws_glossary(nws_csv)
    logger.info(f"Parsed {len(entries)} grouped NWS glossary entries.")

    xml_content = generate_nws_xml(entries, templates_dir)
    output_xml = Path("eaps-dictionary.xml")
    output_xml.write_text(xml_content, encoding="utf-8")
    logger.info(f"Generated XML file '{output_xml.as_posix()}'")

    if no_compile:
        logger.info("Compilation disabled by user.")
        return True

    compiled = compile_dictionary(
        dict_name="Earth and Planetary Science Dictionary",
        dict_id="eaps-dictionary",
        ddk_dir=ddk_dir,
        dest_dir=dest_dir,
        create_symlink=False,
    )
    return compiled


def run_naer_pipeline(
    naer_csv: Path | str,
    templates_dir: Path | str,
    ddk_dir: Path | str = Path(DEFAULT_PATHS["ddk_dir"]),
    dest_dir: Path | str = Path(DEFAULT_PATHS["dest_dir"]),
    no_compile: bool = False,
) -> bool:
    naer_csv = Path(naer_csv)
    templates_dir = Path(templates_dir)
    ddk_dir = Path(ddk_dir)
    dest_dir = Path(dest_dir)

    logger.info(f"Starting NAER Translation pipeline using '{naer_csv.as_posix()}'...")
    if not naer_csv.exists():
        logger.error(f"NAER translation CSV not found at '{naer_csv.as_posix()}'")
        return False

    entries = parse_naer_translations(naer_csv)
    logger.info(f"Parsed {len(entries)} grouped NAER translation entries.")

    xml_content = generate_naer_xml(entries, templates_dir)
    output_xml = Path("eaps-eng-chn-dictionary.xml")
    output_xml.write_text(xml_content, encoding="utf-8")
    logger.info(f"Generated XML file '{output_xml.as_posix()}'")

    if no_compile:
        logger.info("Compilation disabled by user.")
        return True

    compiled = compile_dictionary(
        dict_name="Earth and Planetary Science English-Traditional Chinese Dictionary",
        dict_id="eaps-eng-chn-dictionary",
        ddk_dir=ddk_dir,
        dest_dir=dest_dir,
        create_symlink=True,
    )
    return compiled


def main():
    parser = argparse.ArgumentParser(
        description="Compile Earth and Planetary Science dictionaries for macOS."
    )
    parser.add_argument(
        "--type",
        choices=["nws", "naer", "all"],
        default="all",
        help="Type of dictionary to generate (default: all)",
    )
    parser.add_argument(
        "--templates-dir",
        default="templates",
        help="Directory containing XML templates (default: templates/)",
    )
    parser.add_argument(
        "--nws-csv",
        default="nws-glossary.csv",
        help="Path to the NWS glossary CSV file (default: nws-glossary.csv)",
    )
    parser.add_argument(
        "--naer-csv",
        default="naer-translation.csv",
        help="Path to the NAER translation CSV file (default: naer-translation.csv)",
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
        help="Generate XML files only without compiling them",
    )
    parser.add_argument(
        "--reload-app",
        action="store_true",
        help="Automatically reload Dictionary.app on successful build",
    )

    args = parser.parse_args()

    success = True
    any_compiled = False

    if args.type in ("nws", "all"):
        nws_success = run_nws_pipeline(
            nws_csv=Path(args.nws_csv),
            templates_dir=Path(args.templates_dir),
            ddk_dir=Path(args.ddk_dir),
            dest_dir=Path(args.dest_dir),
            no_compile=args.no_compile,
        )
        success = success and nws_success
        if nws_success and not args.no_compile:
            any_compiled = True

    if args.type in ("naer", "all"):
        naer_success = run_naer_pipeline(
            naer_csv=Path(args.naer_csv),
            templates_dir=Path(args.templates_dir),
            ddk_dir=Path(args.ddk_dir),
            dest_dir=Path(args.dest_dir),
            no_compile=args.no_compile,
        )
        success = success and naer_success
        if naer_success and not args.no_compile:
            any_compiled = True

    if success and any_compiled and args.reload_app:
        reload_dictionary_app()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
