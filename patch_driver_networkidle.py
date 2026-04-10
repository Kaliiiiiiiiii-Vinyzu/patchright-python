"""
Patches the patchright driver's frames.js to exclude captcha polling requests
from networkidle calculations.

Run after the driver has been downloaded (after `pip install -e .` or `setup.py`):
    python patch_driver_networkidle.py

This modifies _inflightRequestStarted and _inflightRequestFinished to skip
requests matching known captcha provider domains, following the same pattern
as the existing _isFavicon exclusion in Playwright's source.

Source: https://github.com/bugbasesecurity/patchright
"""

import re
import sys
from pathlib import Path

CAPTCHA_PATTERNS_JS = '["challenges.cloudflare.com","google.com/recaptcha","www.gstatic.com/recaptcha","hcaptcha.com","api.funcaptcha.com","client-api.arkoselabs.com","google-analytics.com","googletagmanager.com","analytics.google.com","hotjar.com","fullstory.com","logrocket.com","mouseflow.com","clarity.ms","browser-intake-datadoghq.com","sentry.io","newrelic.com","nr-data.net","forter.com","/heartbeat","/keepalive","/keep-alive","/beacon"]'

CAPTCHA_CHECK = f"""const _reqUrl = request.url();
    if ({CAPTCHA_PATTERNS_JS}.some(p => _reqUrl.includes(p)))
      return;"""

PATCH_MARKER = "// [patchright-networkidle-blacklist]"


def find_frames_js() -> Path:
    # Look in playwright-python/patchright/driver/ (post-patch build dir)
    search_roots = [
        Path("playwright-python/patchright/driver"),
        Path("playwright-python/playwright/driver"),
    ]

    for root in search_roots:
        if root.exists():
            candidates = list(root.rglob("**/server/frames.js"))
            if candidates:
                return candidates[0]

    # Fallback: search from current dir
    candidates = list(Path(".").rglob("**/driver/package/lib/server/frames.js"))
    if candidates:
        return candidates[0]

    print("ERROR: Could not find frames.js in driver", file=sys.stderr)
    sys.exit(1)


def patch_method(code: str, method_name: str) -> str:
    pattern = rf'({method_name}\(request\) \{{[^}}]*?if \(request\._isFavicon\)\s*return;)'
    match = re.search(pattern, code, re.DOTALL)

    if not match:
        print(f"ERROR: Could not find {method_name} with _isFavicon check", file=sys.stderr)
        sys.exit(1)

    original = match.group(1)
    patched = original + f"\n    {PATCH_MARKER}\n    {CAPTCHA_CHECK}"
    return code.replace(original, patched, 1)


def main():
    frames_js = find_frames_js()
    code = frames_js.read_text()

    if PATCH_MARKER in code:
        print(f"Already patched: {frames_js}")
        return

    code = patch_method(code, "_inflightRequestStarted")
    code = patch_method(code, "_inflightRequestFinished")

    frames_js.write_text(code)
    print(f"Patched: {frames_js}")
    print(f"Captcha domains excluded from networkidle: {CAPTCHA_PATTERNS_JS}")


if __name__ == "__main__":
    main()
