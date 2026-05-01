import nuke
import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
#  Auto-register My_Gizmos  →  .gizmo files  +  Python custom nodes
#  Auto-register My_Tools   →  .py utility / pipeline scripts
# ─────────────────────────────────────────────────────────────────────────────

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_GIZMO_DIR = os.path.join(_PLUGIN_DIR, "My_Gizmos")
_TOOLS_DIR = os.path.join(_PLUGIN_DIR, "My_Tools")

# Create folders if they don't exist yet
os.makedirs(_GIZMO_DIR, exist_ok=True)
os.makedirs(_TOOLS_DIR, exist_ok=True)

# ── Gizmos: add root + every sub-folder to Nuke's plugin path AND sys.path ───
nuke.pluginAddPath(_GIZMO_DIR)
if _GIZMO_DIR not in sys.path:
    sys.path.insert(0, _GIZMO_DIR)
for root, dirs, _ in os.walk(_GIZMO_DIR):
    dirs[:] = [d for d in sorted(dirs) if not d.startswith((".", "_"))]
    if root != _GIZMO_DIR:
        nuke.pluginAddPath(root)
        if root not in sys.path:
            sys.path.insert(0, root)

# ── Tools: add to both Nuke's plugin path AND Python's sys.path ──────────────
nuke.pluginAddPath(_TOOLS_DIR)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

for root, dirs, _ in os.walk(_TOOLS_DIR):
    dirs[:] = [d for d in sorted(dirs) if not d.startswith((".", "_"))]
    if root != _TOOLS_DIR:
        nuke.pluginAddPath(root)
        if root not in sys.path:
            sys.path.insert(0, root)
