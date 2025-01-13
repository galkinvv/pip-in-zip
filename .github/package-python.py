import sys, pathlib, shutil, zipfile, subprocess
SELF_DIR = pathlib.Path(__file__).absolute().parent

def move_python_distr(full_dir: pathlib.Path, target_dir: pathlib.Path, release_name: str):
    for f in full_dir.iterdir():
        if f.name.lower() == "dlls" or f.suffix.lower() in {".exe", ".dll"}:
            f.rename(target_dir/f.name)

    expected_zip_name = pathlib.Path(next(p for p in sys.path if p.endswith(".zip"))).name

    for sub_dir in ("tcl8.6", "tk8.6"):
        sub_target = target_dir / "tcl" / sub_dir
        sub_target.mkdir(parents=True)
        for f in (full_dir/ "tcl" / sub_dir).iterdir():
            if f.suffix.lower() == ".tcl" or f.name.lower() in {"tclindex", "opt0.4", "ttk"}:
                f.rename(sub_target/f.name)

    idle_target = target_dir / "tcl/idle"
    idle_target.mkdir(parents=True)
    for f in (full_dir/ "Lib/idlelib").iterdir():
        if f.suffix.lower() == ".def" or f.name.lower() in {"icons"}:
            f.rename(idle_target/f.name)

    with zipfile.PyZipFile(target_dir / expected_zip_name, mode="w") as std_lib:
        source_lib = full_dir/"Lib"
        target_lib = target_dir/"Lib"
        target_lib.mkdir()
        std_lib.writepy(source_lib)
        std_lib.writepy(SELF_DIR/"sitecustomize.py")
        
        for package in source_lib.iterdir():
            if package.is_dir():
                if package.name not in {"turtledemo"}: # turtledemo is not worth fixing even for working from .zip
                    std_lib.writepy(package)
        
    launcher = target_dir / "ConsolePIPinZIP.bat"
    launcher_text = launcher.read_text()
    launcher.write_text(launcher_text.replace("%CONSOLE_NAME_PLACEHOLDER%", "PIPinZIP " + release_name))

if __name__ == "__main__":
    full_dir = pathlib.Path(sys.executable).absolute().parent
    target_dir = SELF_DIR.parent
    move_python_distr(full_dir, target_dir, sys.argv[1])
