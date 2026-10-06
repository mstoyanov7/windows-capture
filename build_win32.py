"""Build a win32 wheel with the explicitly selected 32-bit CPython interpreter."""

import argparse
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parent
TARGET = "i686-pc-windows-msvc"


def run(*args, cwd=ROOT, env=None):
    print("+", subprocess.list2cmdline([str(arg) for arg in args]), flush=True)
    subprocess.run([str(arg) for arg in args], cwd=cwd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Install and import-check the wheel in this Python")
    args = parser.parse_args()

    if sys.platform != "win32":
        parser.error("Run this script on Windows.")
    if platform.python_implementation() != "CPython" or sys.version_info < (3, 9):
        parser.error("CPython 3.9 or newer is required; Python 3.11 x86 is recommended.")
    if struct.calcsize("P") != 4:
        parser.error("This is 64-bit Python. Run with the full path to your 32-bit python.exe.")
    for program in ("rustup", "cargo"):
        if shutil.which(program) is None:
            parser.error("Install Rust from https://rustup.rs/ and reopen the terminal.")

    # Explicit values take precedence over inherited cross-compilation settings.
    build_env = os.environ.copy()
    for name in tuple(build_env):
        if name.startswith("PYO3_") or name in ("CARGO_BUILD_TARGET", "MATURIN_PEP517_ARGS"):
            build_env.pop(name)
    build_env["PYO3_PYTHON"] = sys.executable

    run("rustup", "target", "add", TARGET, env=build_env)
    run(sys.executable, "-m", "pip", "install", "--only-binary=:all:", "maturin>=1.3,<2")

    # Isolate output so an earlier wheel can never be mistaken for this build.
    dist = ROOT / "dist" / "win32"
    dist.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="windows-capture-win32-") as temporary:
        run(
            sys.executable, "-m", "maturin", "build", "--release", "--locked",
            "--manifest-path", ROOT / "windows-capture-python" / "Cargo.toml",
            "--target", TARGET, "--interpreter", sys.executable,
            "--out", temporary, env=build_env,
        )
        wheels = list(Path(temporary).glob("windows_capture-*-win32.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected exactly one win32 wheel from maturin.")
        wheel = wheels[0]
        with zipfile.ZipFile(wheel) as archive:
            native_files = [name for name in archive.namelist() if name.endswith(".pyd")]
            if not native_files:
                raise RuntimeError("Wheel contains no native extension.")
            for name in native_files:
                data = archive.read(name)
                pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
                if data[:2] != b"MZ" or data[pe_offset:pe_offset + 4] != b"PE\0\0":
                    raise RuntimeError("Invalid native extension PE header.")
                if struct.unpack_from("<H", data, pe_offset + 4)[0] != 0x014C:
                    raise RuntimeError("Native extension is not an x86 binary.")
        output = dist / wheel.name
        shutil.copy2(wheel, output)

    print("Built:", output)
    if args.install:
        run(sys.executable, "-m", "pip", "install", "--only-binary=:all:", "--force-reinstall", output)
        with tempfile.TemporaryDirectory() as temporary:
            run(
                sys.executable, "-I", "-c",
                "import struct, windows_capture; "
                "assert struct.calcsize('P') == 4; "
                "print('32-bit import OK:', windows_capture.__file__)",
                cwd=temporary,
            )


if __name__ == "__main__":
    main()
