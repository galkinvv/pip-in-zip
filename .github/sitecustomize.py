import sys, os


finder = None
def pip_in_zip_clear_hooks():
    """clears up early installed hooks (if present)"""
    if finder in sys.meta_path:
        sys.meta_path.remove(finder)


def pip_in_zip_tune_extra_for_pip():
    """Tunes environment to be more reloacatable, including some risky changes known to be safe for pip
    mostly enforcing pip avoid hardcoding paths ini generated .exes
    """
    import importlib.util

    print("Arranging PIPinZIP-specifics for `pip` tool")
    if not importlib.util.find_spec("pip"):
        # no newer pip installed - add bundled pip to path with lowest priorityat the end of sys.path
        import importlib.resources, ensurepip, zipimport, _io, io
        class ZipBytesImporter(zipimport.zipimporter):
            paths_bytes_values = {}
            def __init__(self, path=None):
                if path is None:
                    return
                for virtual_path in ZipBytesImporter.paths_bytes_values:
                    if path.startswith(virtual_path):
                        self.prefix = path[len(virtual_path)+1:]
                        self.archive = virtual_path
                        self._files = zipimport._read_directory(self.archive)
                        if self.prefix:
                            self.prefix += os.path.sep
                        return
                raise ImportError("Not ZipBytesImporter prefix")
        zip_bytes_importer_sample_instance = ZipBytesImporter()

        original_open_code = _io.open_code
        def patched_io_open_code(path):
            bytes_data = ZipBytesImporter.paths_bytes_values.get(path)
            if bytes_data:
                return io.BytesIO(bytes_data)
            return original_open_code(path)

        sys.path_hooks.insert(0, ZipBytesImporter)
        _io.open_code = patched_io_open_code

        for f in importlib.resources.contents(ensurepip):
            if f.endswith(".whl"):
                path_entry = os.path.join(os.path.dirname(ensurepip.__file__), f)
                ZipBytesImporter.paths_bytes_values[path_entry] = importlib.resources.read_binary(ensurepip, f)
                sys.path.append(path_entry)

        import pip._vendor.distlib.resources
        pip._vendor.distlib.resources.register_finder(zip_bytes_importer_sample_instance, None)

    if os.path.isabs(sys.executable):
        # make pip happy about scripts directory in path
        os.environ["PATH"] = os.path.dirname(sys.executable) + ";" + os.environ["PATH"]
        # alter the python name embedded in installed launchers to be a plin exe to search in current dir or PATH environ
        sys.executable = os.path.basename(sys.executable)
        if "PIP_CONFIG_FILE" not in os.environ:
            os.environ["PIP_CONFIG_FILE"] = os.devnull #  ignore any local pip configs
            if "PIP_NO_CACHE_DIR" not in os.environ:
                    os.environ["PIP_NO_CACHE_DIR"] = "True" #  dont pollute or use local pip cache


def pip_in_zip_tune():
    """Tunes environment: use packed pip from bundled wheel, organize scheme with putting scripts in base dir"""
    import importlib.util, importlib.abc, sysconfig, site

    pip_in_zip_dir_lower = os.path.abspath(os.path.dirname(sys.executable)).lower() + os.path.sep

    # Remove paths outside of pip_in_zip_dir_lower from sys.path.
    # This ensures better portability eliminating effects from env-level provided PYTHONPATH

    sys.path = [
        p for p in sys.path
        if (os.path.abspath(p) + os.path.sep).lower().startswith(pip_in_zip_dir_lower)
    ]
    site.ENABLE_USER_SITE = False
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
                or (pip_exe_center[0] == 3 and os.path.sep not in pip_exe_center)
            ):
                pip_in_zip_tune_extra_for_pip()
        if sys.argv[0] == "-m":
            import importlib.abc
            __import__("runpy")  # preimport runpy to ensure that next imported package would be the one specified in command line

            class TuneFinder(importlib.abc.MetaPathFinder):
                override_origin = None
                override_for_prefix = ""
                def find_spec(self, fullname, path, target=None):
                    if not self.override_origin:
                        pip_in_zip_clear_hooks()
                        return None
                    finder_index = sys.meta_path.index(finder)
                    for other_finder in sys.meta_path[finder_index + 1:]:
                        try:
                            find_spec = other_finder.find_spec
                        except AttributeError:
                            continue
                        spec = find_spec(fullname, path, target)
                        if spec:
                            tuned_origin = self.mod_path_for_submobule(fullname, spec.origin)
                            if tuned_origin:
                                spec.origin = tuned_origin
                            return spec
                    return None

                def mod_path_for_submobule(self, fullname: str, mod_path:str) -> str:
                    if not fullname.startswith(self.override_for_prefix):
                        return None
                    return os.path.join(self.override_origin, os.path.basename(mod_path))

            class FirstImportInspectFinder(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path, target=None):
                    global finder
                    finder_index = sys.meta_path.index(finder)
                    finder = TuneFinder()
                    sys.meta_path[finder_index] = finder
                    if not path and not target:
                        # import of module specified in command line is executed. Check if it is pip
                        if fullname == "pip":
                            pip_in_zip_tune_extra_for_pip()
                        elif fullname == "idlelib":
                            print("Arranging PIPinZIP-specifics for `idle` tool")
                            finder.override_origin = os.path.join(pip_in_zip_dir_lower, "tcl", "idle")
                            finder.override_for_prefix = "idlelib."
                            import zipimport
                            if not hasattr(zipimport.zipimporter, "exec_module"):
                                # older python uses zipimport.zipimporter.load_module that ignores origin from spec, patch it too
                                import _frozen_importlib_external as _bootstrap_external
                                original_fix_up_module = _bootstrap_external._fix_up_module 
                                def patched_fix_up_module(mod_dict, fullname, mod_path, *args, **kwargs):
                                    mod_path = finder.mod_path_for_submobule(fullname, mod_path) or mod_path
                                    print(mod_path)
                                    original_fix_up_module(mod_dict, fullname, mod_path, *args, **kwargs)
                                _bootstrap_external._fix_up_module = patched_fix_up_module

                    return None

            global finder
            finder = FirstImportInspectFinder()
            sys.meta_path.insert(0, finder)

if "PIP_IN_ZIP_DO_NOTHING" not in os.environ and os.path.isabs(sys.executable):
    pip_in_zip_tune()