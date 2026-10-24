import os
import sys
import textwrap
import traceback


def show_error(tb):
    """Draw the crash text on screen so it can be screenshotted."""
    try:
        base = os.environ.get("ANDROID_PRIVATE", ".")
