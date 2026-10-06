# windows-capture 2.0.1: 32-bit Python build

Based on upstream commit `c7d106448eb9d9b251345c39047711e1cd408ae2`
from https://github.com/NiiightmareXD/windows-capture.
The upstream MIT license is retained in `LICENCE`.

This archive contains modified source, not a precompiled wheel.

## Build and install on Windows

1. Install **32-bit CPython 3.11** from https://www.python.org/downloads/windows/.
   An existing compatible 32-bit Python can also be used. The extension targets
   CPython 3.9+, but NumPy/OpenCV wheel availability also depends on Python version.
2. Install **Visual Studio Build Tools** from
   https://visualstudio.microsoft.com/visual-cpp-build-tools/ with the
   **Desktop development with C++** workload, including the MSVC x86/x64 build
   tools and a Windows SDK.
3. Install Rust using https://rustup.rs/ and reopen the terminal.
4. Extract this archive. Open **Command Prompt**, change into its
   `windows-capture-win32` directory, and run:

   ```bat
   "C:\path\to\32bit\python.exe" build_win32.py --install
   ```

   Replace the example path with your actual 32-bit Python executable.
   If using a virtual environment, pass that environment's `python.exe`.
   Do not run the command with your 64-bit interpreter.

The script adds the Rust x86 target, installs Maturin, builds with the existing
Cargo lockfile, checks the native PE machine type, and writes the wheel to
`dist\win32`. With `--install`, it installs that wheel and its binary dependencies
into the selected Python, then verifies that the installed module imports.
Omit `--install` to build without installing windows-capture.

The wheel filename should be `windows_capture-2.0.1-cp39-abi3-win32.whl`.
To install it later in another compatible **32-bit** Python environment:

```bat
"C:\path\to\32bit\python.exe" -m pip install --only-binary=:all: "dist\win32\windows_capture-2.0.1-cp39-abi3-win32.whl"
```

If the linker is not found, reopen the **x86 Native Tools Command Prompt for
Visual Studio** and run the build command there. If pip cannot find a binary
dependency, use CPython 3.11 x86; binary wheels for NumPy, OpenCV and Maturin
were resolved successfully for that interpreter during preparation.

## GitHub Actions option

The included `.github/workflows/python-win32.yml` builds on a Windows runner
with Python 3.11 x86. It checks the wheel's native architecture, installs/imports
the package, runs native buffer-boundary tests, and uploads the wheel as an
Actions artifact. It can be triggered manually from the Actions tab after this
source is placed in your own repository. No workflow has been run remotely as
part of preparing this archive.

## Changes

- Add `i686-pc-windows-msvc` to the Rust toolchain targets.
- Add `build_win32.py` to explicitly select x86 and reject a 64-bit interpreter.
- Reject mapped Python frame buffers above `isize::MAX` before constructing
  Rust slices or Python buffer views; on x86 this is 2,147,483,647 bytes.
- Add regression tests for padded rows, signed-size limits and multiplication
  overflow, plus a Windows x86 build workflow.
- Preserve the existing Python capture API and upstream dependency versions.

## Validation performed

On a Linux host with Rust 1.99.0:

```text
PYO3_CROSS=1 PYO3_CROSS_PYTHON_VERSION=3.11 cargo check --locked -p windows-capture-python --target i686-pc-windows-msvc
PYO3_CROSS=1 PYO3_CROSS_PYTHON_VERSION=3.11 cargo check --locked -p windows-capture-python --target i686-pc-windows-msvc --tests
```

Both commands passed. Python build-script syntax and repository whitespace
checks passed. Binary dependencies resolved for CPython 3.11 win32.

These are cross-target compilation checks; they do not link a Windows wheel
or execute the Windows tests. The build script, native test execution, module
import and actual GPU/window capture still require validation on Windows.
