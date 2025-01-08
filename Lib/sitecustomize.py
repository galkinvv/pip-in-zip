import sys, os


def pip_in_zip_tune_extra_for_pip():
    """Tunes environment to be more reloacatable, including some risky changes known to be safe for pip
    mostly enforcing pip avoid hardcoding paths ini generated .exes
    """
    print("Arranging PIPinZIP-specifics for `pip` tool")
    # make pip happy about scripts directory in path
    os.environ["PATH"] = os.path.dirname(sys.executable) + ";" + os.environ["PATH"]
    sys.executable = ".\\" + os.path.basename(sys.executable)  # alters the python name embedded in installed launchers


def pip_in_zip_tune():
    """Tunes environment: use packed pip from bundled wheel, organize scheme with putting scripts in base dir"""
    import importlib.util, sysconfig

    pip_in_zip_dir_lower = os.path.abspath(os.path.dirname(sys.executable)).lower() + "\\"

    # Remove paths outside of pip_in_zip_dir_lower from sys.path.
    # This ensures better portability eliminating effects from env-level provided PYTHONPATH

    sys.path = [
        p for p in sys.path
        if (os.path.abspath(p) + "\\").lower().startswith(pip_in_zip_dir_lower)
    ]

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
            # some module is executed, detect which
            if hasattr(sys, "orig_argv"):
                passed_args = sys.orig_argv[1:]
            else:  # <= py 3.9
                import ctypes

                argv = ctypes.POINTER(ctypes.c_wchar_p)()
                argc = ctypes.c_int()

                ctypes.pythonapi.Py_GetArgcArgv(ctypes.byref(argc), ctypes.byref(argv))
                passed_args = argv[1 : argc.value]
            found_prefix = ""
            for passed_arg in passed_args:
                # module invocation found. If it is pip - run extras, otherwise stop searching
                if found_prefix + passed_arg == "-mpip":
                    pip_in_zip_tune_extra_for_pip()
                    # pip module invocation found, stop searching
                    break
                if found_prefix:
                    # module invocation found, but is not pip, stop searching
                    break
                if passed_arg == "-m":
                    found_prefix = passed_arg


if "PIP_IN_ZIP_DO_NOTHING" not in os.environ and os.path.isabs(sys.executable):
    pip_in_zip_tune()