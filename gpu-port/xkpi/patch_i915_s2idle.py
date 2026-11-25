"""Apply the macOS s2idle override at i915's late system-suspend decision."""
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
source = path.read_text()
declaration = "extern bool nmx_i915_select_s2idle(bool original);"

if declaration not in source:
    function = re.search(
        r"(?m)^static\s+int\s+i915_drm_suspend_late\s*\([^;{}]*\)\s*\{", source
    )
    if not function:
        sys.exit(f"ERROR: i915_drm_suspend_late definition not found in {path}")
    end = re.search(r"(?m)^\}", source[function.end():])
    if not end:
        sys.exit(f"ERROR: end of i915_drm_suspend_late not found in {path}")

    body_end = function.end() + end.start()
    body = source[function.end():body_end]
    condition = r"acpi_target_system_state\(\)\s*<\s*ACPI_STATE_S3\b"
    body, count = re.subn(condition, r"nmx_i915_select_s2idle(\g<0>)", body)
    if count != 1:
        sys.exit(f"ERROR: expected one S3 comparison in i915_drm_suspend_late, found {count}")

    source = (
        source[:function.start()] + declaration + "\n\n"
        + source[function.start():function.end()] + body + source[body_end:]
    )
    path.write_text(source)
