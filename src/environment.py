import _logging
import os
import shutil
import sys

logger = _logging.getLogger(__name__)


def sanitizePath(string: str) -> str:
    if not isinstance(string, str):
        logger.warning("'%s' is '%s', not str!", string, type(string))
        return string
    subs = [
        (os.environ.get("USER", "USER"), "USER"),
        (os.environ.get("USERDOMAIN", "USERDOMAIN"), "DOMAIN")
    ]
    string2 = string
    for pat, repl in subs:
        string2 = string2.replace(pat, repl)
    return string2


platform: str = os.name
platform_long: str = os.environ.get("OS")

try:
    logger.debug("Running script %s", [sanitizePath(v) for v in sys.argv])
    logger.debug("Running python '%s'", sys.version)
    logger.debug("from '%s' ('%s')", sanitizePath(sys.executable), sanitizePath(os.environ.get("_", "!no_")))
    logger.debug("Platform: %s (%s), terminal '%s'", platform, platform_long, os.environ.get("TERM", "!noterm"))
    logger.debug("PWD '%s'", sanitizePath(os.environ.get("PWD", "!nopwd")))
except:
    logger.error("Environment error!", exc_info=True)


def isWindows() -> bool:
    return (platform == "nt")


def isPosix() -> bool:
    return (platform == "posix")


def getGamedirRoot() -> str:
    # Todo: find pesterquest in non-default locations
    if isWindows():
        gamedir_root = "C:/Program Files (x86)/Steam/steamapps/common/Homestuck Pesterquest"
    elif isPosix():
        # If you're on linux, change this path to your steam install directory.
        gamedir_root = os.environ["HOME"] + "/Library/Application Support" + "/Steam/steamapps/common/Homestuck Pesterquest"
    else:
        raise Exception("Unknown platform " + platform)

    return gamedir_root


def getExecutablePostfix() -> str:
    if isWindows():
        return ".exe"
    elif isPosix():
        return ""
    else:
        raise Exception("Unknown platform " + platform)


def getExecutableName() -> str:
    return "pesterquest" + getExecutablePostfix()


def where(target, extradirs=None) -> str:
    extradirs: list = extradirs or []
    which: str = shutil.which(target)

    if not which and extradirs:
        paths = ";".join(extradirs)
        which = shutil.which(target, paths)

    return which


def getGitPath() -> str:
    gitpaths = []
    return where("git", gitpaths)


def getPython3Path():
    for name in ["py", "py3", "python3", "python"]:
        py = where(name)
        if py:
            return py
    return None


def tellBestPy3Cmd():
    best_py3_cmd = getPython3Path()
    if best_py3_cmd:
        a, b = os.path.split(best_py3_cmd)
        if a in sys.path:
            best_py3_cmd = os.path.splitext(b)[0]
        logger.debug("Best python3 command: '%s'", best_py3_cmd)
    else:
        logger.warning("Couldn't find any python launcher in current context?")


tellBestPy3Cmd()
