from pathlib import Path
import shutil
import subprocess

import logging

logger = logging.getLogger(__name__)


def compile_dictionary(
    dict_name: str,
    dict_id: Path | str,
    css_path: Path | str | None = None,
    ddk_dir: Path | str = Path("/Applications/Utilities/DictionaryDevelopmentKit"),
    dest_dir: Path | str = Path("~/Library/Dictionaries"),
    create_symlink: bool = False,
    cwd: Path | str = Path("."),
) -> bool:
    """
    Compiles the dictionary using the Apple Dictionary Development Kit (DDK).

    Equivalent to executing makeeapsdict.sh or makeeapstrans.sh.
    """
    ddk_dir = Path(ddk_dir)
    dest_dir = Path(dest_dir)
    cwd = Path(cwd)

    build_dict_sh = ddk_dir / "bin" / "build_dict.sh"

    if not build_dict_sh.exists():
        logger.warning(
            f"Apple Dictionary Development Kit build script not found at '{build_dict_sh.as_uri}'.\n"
            "Dictionary compilation skipped. Only XML source files were generated."
        )
        return False

    expanded_dest_dir = dest_dir.expanduser()
    dest_bundle_path = expanded_dest_dir / f"{dict_name}.dictionary"
    local_bundle_path = cwd / f"{dict_name}.dictionary"
    objects_dir = cwd / "objects"
    compiled_bundle_path = objects_dir / f"{dict_name}.dictionary"

    # Command arguments for build_dict.sh
    # $DICT_BUILD_TOOL_BIN/build_dict.sh $DICT_BUILD_OPTS "$DICT_NAME" $DICT_ID.xml $DICT_ID.css $DICT_ID.plist
    if css_path is None:
        css_path = Path(f"{dict_id}.css")
        assert css_path.exists(), f"The style sheet {css_path} cannot be found."
    elif isinstance(css_path, str):
        css_path = Path(css_path)
    cmd = [
        build_dict_sh.as_posix(),
        dict_name,
        f"{dict_id}.xml",
        css_path.as_posix(),
        f"{dict_id}.plist",
    ]

    logger.info(f"Running build command: {' '.join(cmd)}")

    try:
        # Run compilation
        result = subprocess.run(
            cmd,
            cwd=cwd.as_posix(),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Compilation failed with exit code {e.returncode}")
        logger.error(e.stderr)
        return False

    # Perform file movements as in shell scripts
    try:
        # Remove old local and destination bundles
        if local_bundle_path.exists():
            if local_bundle_path.is_symlink():
                local_bundle_path.unlink()
            else:
                shutil.rmtree(local_bundle_path)

        if dest_bundle_path.exists():
            shutil.rmtree(dest_bundle_path)

        # Create destination directory if it doesn't exist
        expanded_dest_dir.mkdir(parents=True, exist_ok=True)

        # Move the compiled dictionary bundle from objects/ to DESTINATION_FOLDER
        if compiled_bundle_path.exists():
            logger.info(
                f"Moving compiled bundle from '{compiled_bundle_path}' to '{dest_bundle_path}'"
            )
            shutil.move(compiled_bundle_path, dest_bundle_path)
        else:
            logger.error(f"Compiled bundle not found at '{compiled_bundle_path}'")
            return False

        # If requested, create a symlink in the current working directory pointing to the compiled bundle
        if create_symlink:
            logger.info(
                f"Creating local symlink '{local_bundle_path}' -> '{dest_bundle_path}'"
            )
            local_bundle_path.symlink_to(dest_bundle_path)

    except Exception as e:
        logger.error(f"Failed to perform post-compilation file operations: {e}")
        return False
    finally:
        # Clean up temporary objects/ directory
        if objects_dir.exists():
            logger.info(f"Cleaning up objects directory: '{objects_dir}'")
            shutil.rmtree(objects_dir)

    logger.info(f"Successfully compiled and installed '{dict_name}'")
    return True
