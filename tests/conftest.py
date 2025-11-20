import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

name: CI

on:
  push:
  pull_request:

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: [3.9, 3.10, 3.11]
    runs-on: ${{ matrix.os }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies (Linux/macOS)
        if: runner.os != 'Windows'
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
        shell: bash

      - name: Install dependencies (Windows)
        if: runner.os == 'Windows'
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          python -m pip install pywin32
        shell: powershell

      - name: Start Xvfb on Linux
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y xvfb
          Xvfb :99 -screen 0 1280x1024x24 &>/dev/null &
          export DISPLAY=:99
        shell: bash

      - name: Run tests
        env:
          SKIP_WIN32: ${{ runner.os != 'Windows' }}
        run: |
          python -m pytest -q
        shell: bash

      - name: Upload test logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-log-${{ matrix.os }}-${{ matrix.python-version }}
          path: records/error_log.txt

# Skip tests marked with `requires_win32` when SKIP_WIN32 env var is true.
skip_win32 = os.getenv("SKIP_WIN32", "True").lower() in ("1", "true", "yes")

def pytest_collection_modifyitems(config, items):
    if skip_win32:
        for item in list(items):
            if "requires_win32" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="win32 tests skipped on this runner"))
