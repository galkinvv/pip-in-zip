import sys, os


pip_finder = None
def pip_in_zip_clear_hooks():
    """clears up early installed hooks (if present)"""
    if pip_finder in sys.meta_path:
        sys.meta_path.remove(pip_finder)


def pip_in_zip_tune_extra_for_pip():
    """Tunes environment to be more reloacatable, including some risky changes known to be safe for pip
    mostly enforcing pip avoid hardcoding paths ini generated .exes
    """
    print("Arranging PIPinZIP-specifics for `pip` tool")
    if os.path.isabs(sys.executable):
        # make pip happy about scripts directory in path
        os.environ["PATH"] = os.path.dirname(sys.executable) + ";" + os.environ["PATH"]
        # alter the python name embedded in installed launchers to be a plin exe to search in current dir or PATH environ
        sys.executable = os.path.basename(sys.executable)
        if "PIP_CONFIG_FILE" not in os.environ:
            os.environ["PIP_CONFIG_FILE"] = os.devnull #  ignore any local pip configs
            if "PIP_NO_CACHE_DIR" not in os.environ:
                    os.environ["PIP_NO_CACHE_DIR"] = "True" #  dont pollute or use local pip cache
    pip_in_zip_clear_hooks()


def pip_in_zip_tune():
    """Tunes environment: use packed pip from bundled wheel, organize scheme with putting scripts in base dir"""
    import importlib.util, importlib.abc, sysconfig, site

    pip_in_zip_dir_lower = os.path.abspath(os.path.dirname(sys.executable)).lower() + "\\"

    # Remove paths outside of pip_in_zip_dir_lower from sys.path.
    # This ensures better portability eliminating effects from env-level provided PYTHONPATH

    sys.path = [
        p for p in sys.path
        if (os.path.abspath(p) + "\\").lower().startswith(pip_in_zip_dir_lower)
    ]
    site.ENABLE_USER_SITE = False

    if not importlib.util.find_spec("pip"):
        # no newer pip installed - add bundled pip to path with lowest priority
        ensurepip_whl_dir = importlib.util.find_spec("ensurepip").submodule_search_locations[0] + "\\_bundled\\"
        for f in os.listdir(ensurepip_whl_dir):
            if f.endswith(".whl"):
                sys.path.append(ensurepip_whl_dir + f)

    sysconfig._PIP_USE_SYSCONFIG = True  # use sysconfig instead of distutils even in 3.9
    sysconfig._INSTALL_SCHEMES["nt"]["scripts"] = "{base}"  # alters the launchers directory
    
    if sys.argv:
        pip_exe_prefix = pip_in_zip_dir_lower + "pip"
        pip_exe_suffix = ".exe"

        sys_argv0_lower = sys.argv[0].lower()
        if sys_argv0_lower.startswith(pip_exe_prefix) and sys_argv0_lower.endswith(pip_exe_suffix):
            # file named like pip.exe/pip3*.exe is executed
            pip_exe_center = sys_argv0_lower[len(pip_exe_prefix) : -len(pip_exe_suffix)]
            if (
                not pip_exe_center
                or (pip_exe_center[0] == 3 and "\\" not in pip_exe_center)
            ):
                pip_in_zip_tune_extra_for_pip()
        if sys.argv[0] == "-m":
            import runpy  # preimport runpy to ensure that next imported package would be the one specified in command line

            class PipFinder(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path, target=None):
                    if not path and not target:
                        # import of module specified in command line is executed. Check if it is pip
                        if fullname == "pip":
                            pip_in_zip_tune_extra_for_pip()
                        else:
                            pip_in_zip_clear_hooks
                    return None

            global pip_finder
            pip_finder = PipFinder()
            sys.meta_path.insert(0, pip_finder)

if "PIP_IN_ZIP_DO_NOTHING" not in os.environ and os.path.isabs(sys.executable):
    pip_in_zip_tune()