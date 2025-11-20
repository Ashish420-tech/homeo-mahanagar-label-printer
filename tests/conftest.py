# tests/conftest.py
import os
import sys
import shutil
import subprocess
import pytest

env = os.getenv("SKIP_WIN32")
if env is None:
    skip_win32 = not sys.platform.startswith("win")
else:
    skip_win32 = str(env).lower() in ("1", "true", "yes")


def pytest_collection_modifyitems(config, items):
    if skip_win32:
        for item in list(items):
            if "requires_win32" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="win32 tests skipped on this runner"))


_xvfb_proc = None


def _start_xvfb_if_needed():
    if not sys.platform.startswith("linux"):
        return None
    if os.environ.get("DISPLAY"):
        return None
    xvfb_bin = shutil.which("Xvfb") or shutil.which("xvfb-run")
    if not xvfb_bin:
        return None
    try:
        if os.path.basename(xvfb_bin).lower().startswith("xvfb-run"):
            proc = subprocess.Popen([xvfb_bin, "--auto-servernum", "--server-args='-screen 0 1280x1024x24'", "sleep", "600"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            os.environ.setdefault("DISPLAY", ":99")
            return proc
        else:
            proc = subprocess.Popen([xvfb_bin, ":99", "-screen", "0", "1280x1024x24"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            os.environ.setdefault("DISPLAY", ":99")
            return proc
    except Exception:
        return None


def pytest_sessionstart(session):
    global _xvfb_proc
    _xvfb_proc = _start_xvfb_if_needed()
    if _xvfb_proc:
        session.config._xvfb_started = True
    else:
        session.config._xvfb_started = False


def pytest_sessionfinish(session, exitstatus):
    global _xvfb_proc
    if _xvfb_proc:
        try:
            _xvfb_proc.terminate()
            _xvfb_proc.wait(timeout=5)
        except Exception:
            try:
                _xvfb_proc.kill()
            except Exception:
                pass
        _xvfb_proc = None
