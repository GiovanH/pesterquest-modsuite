#! python3

# This is the main script that patches custom resources into the main game.

# import subprocess
import os
import glob
import json
import shutil
# import collections
import _logging
import environment
# import zipfile
import zlib
import fse_mod
from util import copyTreeLazy

logger = _logging.getLogger(__name__)

platform = os.name

gamedir_root = os.path.normpath(os.path.join("..", "projects", "work"))
executable = environment.getExecutableName()

gamedir = os.path.normpath(os.path.join(gamedir_root, "game"))

litearch = "lite.zip"
litedir = "lite"
skinbase = "../skins"
# Properties, dependent on the current gamedir


def getCustomScriptsDir():
    return os.path.join(gamedir, "custom_scripts")


def getCommonAssetsDir():
    return os.path.join(gamedir, "custom_assets")


def print_tree(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        logger.info('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            logger.info('{}{}'.format(subindent, f))


def copy2(src, dst, verbose=False):
    printer = logger.info if verbose else logger.debug
    try:
        shutil.copy2(src, dst)
        printer("{} --> {}".format(src, dst))
    except Exception:
        printer("{} -x> {}".format(src, dst))
        raise


def mergeDirIntoDir(src, dst, verbose=False):
    printer = logger.info if verbose else logger.debug
    try:
        copyTreeLazy(src, dst)
        printer("{} --> {}".format(src, dst))
        # if verbose:
        #     print_tree(src)
    except Exception:
        printer("{} -x> {}".format(src, dst))
        raise


def merge_lists(a, b):
    return list(set(a).union(b))


def dict_merge(dct, merge_dct):
    for k, v in merge_dct.items():
        if k in dct:
            if isinstance(dct[k], dict) and isinstance(merge_dct[k], dict):
                dict_merge(dct[k], merge_dct[k])
            elif isinstance(dct[k], list) and isinstance(merge_dct[k], list):
                dct[k] = merge_lists(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def crcFile(file_name):
    prev = 0
    for eachLine in open(file_name, "rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%X" % (prev & 0xFFFFFFFF)


# def ensureLiteAvailable(litedir):
#     needs_extract = True
#     zipcrc_path = os.path.join(litedir, ".litecrc")
#     real_crc = crcFile(litearch)
#     if os.path.isfile(zipcrc_path):
#         with open(zipcrc_path, "r") as fp:
#             cache_crc = fp.read()
#         if real_crc == cache_crc:
#             needs_extract = False
#             logger.info(f"Skipping extraction: CRC match at '{zipcrc_path}'")
#         else:
#             logger.info(f"Bad CRC cache found at '{zipcrc_path}'")
#     else:
#         logger.info(f"No CRC cache found at '{zipcrc_path}'")

#     if needs_extract:
#         logger.info(f"Extracting '{litearch}' to '{litedir}'")
#         with zipfile.ZipFile(litearch, "r") as z:
#             z.extractall(litedir)
#         with open(zipcrc_path, "w") as fp:
#             fp.write(real_crc)


def copyLiteWithSkins(destdir, skins=None):
    skins = skins or []
    logger.info("Copying PQ lite")
    lite_metadata_path = os.path.join(destdir, "fse_lite_meta.json")

    # ensureLiteAvailable(litedir)

    expected_metadata = skins
    # if os.path.isfile(lite_metadata_path):
    #     try:
    #         with open(lite_metadata_path, "r") as fp:
    #             real_metadata = json.load(fp)
    #         # if expected_metadata == real_metadata:
    #         #     logger.info("Skin settings unchanged.")
    #         #     return
    #     except json.decoder.JSONDecodeError:
    #         logger.error("Metadata cache corrupted")

    copyTreeLazy(litedir, destdir)

    logger.info("Patching skins")
    for skin in ["default", *skins]:
        skindir = os.path.join(skinbase, skin)
        if not os.path.isdir(skindir):
            logger.error("Skin not found: %s", skin)
            logger.error("Should be located at %s", skindir)
            raise FileNotFoundError(skindir)
        copyTreeLazy(skindir, destdir)

    with open(lite_metadata_path, "w", encoding="utf-8") as fp:
        json.dump(expected_metadata, fp)


def copyAndSubRpy(src, dst, metadata, verbose=False):
    printer = logger.info if verbose else logger.debug

    if not os.path.isfile(src):
        raise FileNotFoundError(src)
    # if os.path.isfile(dst):
    #     raise FileExistsError(dst)

    try:
        with open(src, "r", encoding="utf-8") as fp:
            rpy_data = fp.read()
    except UnicodeDecodeError:
        logger.error(f"Can't read input file '{src}' as utf-8. Make sure it's saved as a utf-8 compatable format, like utf-8 or ascii.")
        raise

    try:
        rpy_data = fse_mod.subtableReplace(rpy_data, metadata)
        with open(dst, 'w', encoding="utf-8") as fp:
            fp.write(rpy_data)
        printer("{} --> {}".format(src, dst))
    except Exception:
        printer("{} -x> {}".format(src, dst))
        raise


def processPackages(only_volumes=None, verbose=False):
    only_volumes = only_volumes or []
    all_packages, warn = fse_mod.getAllPackages("..", only_volumes)
    for package in all_packages:
        logger.info(f"Patching {package.id}")

        # Copy precompiled RPA archives
        for rpa in package.getArchiveFiles():
            __, filename = os.path.split(rpa)
            destfile = os.path.join(gamedir, (f"ycustom_{package.id}_{filename}"))
            copy2(rpa, destfile, verbose=verbose)

        # Parse and copy rpy files
        for rpy in package.getScriptFiles():
            __, filename = os.path.split(rpy)
            destfile = os.path.join(getCustomScriptsDir(), f"{package.id}_{filename}")
            copyAndSubRpy(rpy, destfile, package.metadata, verbose=verbose)

        # Copy namespaced assets
        if os.path.isdir(package.assets_dir):
            destdir = os.path.join(gamedir, f"custom_assets_{package.id}")
            # os.makedirs(destdir, exist_ok=True)
            mergeDirIntoDir(package.assets_dir, destdir, verbose=verbose)

        # Copy common assets
        if os.path.isdir(package.assets_common_dir):
            mergeDirIntoDir(package.assets_common_dir, getCommonAssetsDir(), verbose=verbose)

    return (all_packages, warn,)


def patchCreditsData(all_packages):
    # Credits
    all_credits = {}

    for package in all_packages:
        if package.credits:
            dict_merge(all_credits, package.credits)

    # pprint(all_credits)

    with open(os.path.join(getCustomScriptsDir(), "fse_credits.rpy"), 'w', encoding="utf-8") as fp:
        fp.write("init offset = 1\n\n")
        fp.write("define fse_credits_data = ")
        fp.write(json.dumps(all_credits, indent=4))


def patchVolumeData(all_packages):
    # Volume select screen

    all_volumes = sum((p.volumes for p in all_packages), [])

    with open(os.path.join(getCustomScriptsDir(), "fse_volumes_data.rpy"), 'w', encoding="utf-8") as fp:
        fp.write("init offset = 1\n\n")
        fp.write("define fse_volume_data = ")
        fp.write(json.dumps(all_volumes, indent=4))


def patchWarningData(all_packages):
    # Volume select screen

    all_volumes = sum((p.volumes for p in all_packages), [])
    all_warnings = {v["title"]: v["warnings"] for v in all_volumes if v.get("warnings")}

    with open(os.path.join(getCustomScriptsDir(), "fse_warning_data.rpy"), 'w', encoding="utf-8") as fp:
        fp.write("init offset = 1\n\n")
        fp.write("define fse_warning_data = ")
        fp.write(json.dumps(all_warnings, indent=4))


def patchMusicData(all_packages):
    # Volume select screen

    all_music = {t["_file"]: t for t in sum((p.music for p in all_packages), [])} 

    with open(os.path.join(getCustomScriptsDir(), "fse_music_data.rpy"), 'w', encoding="utf-8") as fp:
        fp.write("init offset = 1\n\n")
        fp.write("define fse_music_data = ")
        fp.write(json.dumps(all_music, indent=4))


def patchAchievementsData(all_packages):
    # Volume select screen
    sorted_packages = sorted(all_packages, key=lambda p: (p.metadata["package_id"]))
    all_achievements = sum((p.achievements for p in sorted_packages), [])

    # TODO sort this properly! author/package/volume

    with open(os.path.join(getCustomScriptsDir(), "fse_achievement_data.rpy"), 'w', encoding="utf-8") as fp:
        fp.write("init offset = 1\n\n")
        fp.write("define fse_achievements_data = ")
        fp.write(json.dumps(all_achievements, indent=4))

    # with open(os.path.join(getCustomScriptsDir(), "ach_loc_english.vdf"), 'w', encoding="utf-8") as fp:
#         fp.write(""""lang"
# {
#     "Language"  "english"
#     "Tokens"
#     {\n""")
#         for i, ach in enumerate(all_achievements):
#             fp.write(f'        "NEW_ACHIEVEMENT_1_{i}"  "{ach.get("_id")}"\n')
#             fp.write(f'        "NEW_ACHIEVEMENT_1_{i}_NAME"  "{ach.get("name")}"\n')
#             fp.write(f'        "NEW_ACHIEVEMENT_1_{i}_DESC"  "{ach.get("hint") or ach.get("desc")}"\n')

#         fp.write("\n    }\n}")

    with open(os.path.join(getCustomScriptsDir(), "ach_meta.txt"), 'w', encoding="utf-8") as fp:
        for i, ach in enumerate(all_achievements):
            fp.write(ach.get("_id") + "\n")
            fp.write(ach.get("name") + "\n")
            fp.write((ach.get("hint") or ach.get("desc")) + "\n")
            fp.write(ach.get("_img_unlocked") + "\n")
            fp.write(ach.get("_img_locked") + "\n")
            fp.write("\n")

def writeBuildOpts(all_packages):
    # Build options

    with open(os.path.join(getCustomScriptsDir(), "fse_buildopts.rpy"), 'w', encoding="utf-8") as fp:
        fp.write("init 1 python:\n")
        # fp.write(f"    build.classify(\"game/fse_packagelist.json\", None) \n")
        fp.write(f"    build.classify(\"fse_lite_meta.json\", None) \n")
        fp.write(f"    build.classify(\"game/custom_assets/**\", \"archive\") \n")
        for package in all_packages:
            ar = f"ar_{package.id}"
            fp.write(f"    build.archive(\"{ar}\")\n")
            fp.write(f"    build.classify(\"game/custom_assets_{package.id}/**\", \"{ar}\") \n")


def makeArgParser():
    import argparse
    ap = argparse.ArgumentParser()
    # ap.add_argument(
    #     "--nolaunch", action="store_true",
    #     help="Don't launch the game, only patch the assets. Useful during development for real-time reloading.")
    ap.add_argument(
        "--verbose", action="store_true",
        help="Print more output about successful operations.")
    ap.add_argument(
        "--pause", action="store_true",
        help="Pause before launching the game OR pause when script is complete.")
    ap.add_argument(
        "--clean", action="store_true",
        help="Delete old custom assets, including any old mods. Skipped by default for performance.")
    ap.add_argument(
        "--patchdir",
        help="Patch files to this directory, instead of using a standalone installation.'")
    # ap.add_argument(
    #     "--lite", action="store_true",
    #     help="Lite mode: Installs a working version of PQLite, if it doesn't exist, and sets --patchdir to it. Much faster on subsequent runs.")
    ap.add_argument(
        "--skins", nargs="+", default=[],
        help="Skins, found in skins. Loaded in order.")
    ap.add_argument(
        '--packages', nargs="+", default=[],
        help="If set, only look at custom packages with these IDs. By default, all mods in 'custom_volumes' are included, but if this option is set, the patcher only includes the packages specified."
    )
    return ap


def main(argstr=None):

    ap = makeArgParser()

    args = (ap.parse_args(argstr) if argstr else ap.parse_args())
    logger.debug(argstr)
    logger.debug(args)

    # By default, use litemode.
    # If lite isn't ready, copy and extract

    if args.patchdir:
        # Patch to manual folder
        global gamedir_root
        global gamedir
        gamedir_root = args.patchdir
        gamedir = os.path.normpath(os.path.join(gamedir_root, "game"))
        os.makedirs(gamedir, exist_ok=True)
    else:
        # Lite installation
        os.makedirs(gamedir_root, exist_ok=True)
        copyLiteWithSkins(gamedir_root, args.skins)

    logger.debug(f"Working gamedir_root: '{gamedir_root}'")

    # Ensure gamedir_root exists.
    # This can fail if --patchdir is set incorrectly
    # OR if environment failed to detect the right steam library path.
    if not os.path.isdir(gamedir_root):
        logger.error("gamedir_root '%s' not found!", gamedir_root)
        logger.error("Pesterquest may not be installed, or may be in another location.")
        logger.error("Please adjust --patchdir as needed, or use --lite if you do not own pesterquest.")

    if args.packages:
        packagelist_path = os.path.join(gamedir, "fse_packagelist.json")
        new_packagelist = list(args.packages)
        if os.path.isfile(packagelist_path):
            try:
                with open(packagelist_path, "r") as fp:
                    old_packagelist = json.load(fp)
                if any(p not in new_packagelist for p in old_packagelist):
                    logger.info("Some packages removed")
                    args.clean = True
                else:
                    logger.info("Package selections unchanged")
                    args.clean = False or args.clean
            except json.decoder.JSONDecodeError:
                logger.error("Can't read old packagelist")
                args.clean = True
        else:
            logger.error("Missing old packagelist")
            args.clean = True

        with open(packagelist_path, "w") as fp:
            json.dump(new_packagelist, fp)
        
    verbosePrinter = logger.info if args.verbose else logger.debug

    try:

        logger.info("Clearing old scripts")
        try:
            shutil.rmtree(getCustomScriptsDir())
        except FileNotFoundError:
            pass

        # Legacy:
        for rpy in glob.glob(os.path.join(gamedir, "*custom_*.rpy*")):
            verbosePrinter(f"{rpy} --> [X]")
            os.unlink(rpy)

        if args.clean:
            logger.info("Cleaning out old assets")
            for assets_dir in glob.glob(os.path.join(gamedir, "custom_assets_*/")):
                shutil.rmtree(assets_dir, ignore_errors=True)

        logger.info("Initializing")
        os.makedirs(os.path.join("../custom_volumes"), exist_ok=True)
        os.makedirs(os.path.join("../custom_volumes_other"), exist_ok=True)
        os.makedirs(getCustomScriptsDir(), exist_ok=True)

        logger.info("Copying user scripts")
        (all_packages, warn,) = processPackages(only_volumes=args.packages, verbose=args.verbose)

        logger.info("Patching volume select data")
        patchVolumeData(all_packages)
        logger.info("Patching credits data")
        patchCreditsData(all_packages)
        # logger.info("Patching warning data")
        # patchWarningData(all_packages)
        logger.info("Patching achievements data")
        patchAchievementsData(all_packages)
        logger.info("Patching music data")
        patchMusicData(all_packages)
        logger.info("Writing build options")
        writeBuildOpts(all_packages)

        if warn:
            logger.warning("!!!!!!!!!!!!!!!!!!!!!!!!! Errors/warnings occured! Please review the log above for [WARN] or [ERROR] messages.")
            logger.warning("A full logfile should be availible at 'latest_debug.log'")

        # if warn or args.pause:
        #     logger.warning("Please review this window and then press enter to launch the game OR press Ctrl+C to abort.")
        #     input()

        # if not args.nolaunch:
        #     runGame()
    except Exception:
        logger.error("Root exception", exc_info=True)
        logger.warning("A full logfile should be availible at 'latest_debug.log'")
        logger.warning("Please review this window and then press enter to launch the game OR press Ctrl+C to abort.")
        input()
        return


if __name__ == "__main__":
    main()
