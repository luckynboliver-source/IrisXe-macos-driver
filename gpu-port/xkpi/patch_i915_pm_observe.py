"""Instrument the pinned i915 source during the existing all-i915 build."""
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
source = path.read_text()
marker = "/* NMXPM observational hooks */"
if marker not in source:
    for function, value in (
        ("intel_power_domains_suspend", "s2idle"),
        ("intel_power_domains_resume", "-1"),
    ):
        pattern = rf"((?:static\s+)?void\s+{function}\s*\([^;{{}}]*\)\s*\{{)"
        matches = list(re.finditer(pattern, source))
        if len(matches) != 1:
            sys.exit(f"Expected one definition of {function} in {path}")
        match = matches[0]
        if value == "s2idle" and not re.search(r"\bbool\s+s2idle\b", match[0]):
            sys.exit(f"Unexpected s2idle parameter in {function}")
        hook = f'\n\textern void nmx_pm_observe(const char *, int);\n\tnmx_pm_observe("{function}", {value});\n'
        source = source[:match.end()] + hook + source[match.end():]
    path.write_text(marker + "\n" + source)
