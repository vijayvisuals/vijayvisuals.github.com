"""
LightMixer Enhanced Utilities
==============================
Companion module for LightMixer.gizmo

Extended features:
  - Preset System (Save / Load / Delete light mix recipes)
  - Per-Light Temperature Control (Kelvin-based color temperature)
  - Auto-Detect Light AOVs (batch add by naming convention)
  - Group / Layer System (organize and batch-operate on light groups)
  - Undo-Friendly Reset Per Light
  - Light Preview (solo + view in Viewer)
  - AOV Reordering (move up / down in the properties panel)
  - Contact Sheet generation

Original LightMixer gizmo by Harut Harutyunyan (har8unyan)
"""

import nuke
import nukescripts
import os
import json
import math


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

_PRESET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "LightMixer_presets")

_EXCLUSION_SET = {
    "depth", "rgb", "rgba", "alpha", "N", "P", "Pref",
    "motionvector", "UV", "uv", "id", "mask", "Z",
    "normals", "position", "st",
}

_LIGHT_PREFIXES = [
    "lgt_", "light_", "RGBA_", "direct_", "indirect_",
    "diffuse_", "specular_", "emission_", "sss_", "coat_",
    "sheen_", "transmission_", "beauty_", "albedo_",
    "reflect_", "refract_",
]

_LIGHT_KEYWORDS = [
    "light", "lgt", "lamp", "illumin", "direct", "indirect",
    "diffuse", "specular", "emission", "beauty",
]

# All possible per-AOV knob suffixes (for cleanup / serialization)
_AOV_SUFFIXES = [
    "_tex", "_about", "_solo", "_mute", "_dis", "_inject",
    "_reset", "_preview", "_up", "_dn", "_del",
    "_col", "_intens", "_expo", "_temp", "_tempr", "_tempg", "_tempb",
    "_gam", "_sat", "_grp", "_div",
]

# Suffixes carrying user-editable values (for presets / reset)
_VALUE_SUFFIXES = [
    "_col", "_intens", "_expo", "_temp", "_gam", "_sat",
    "_mute", "_solo", "_dis", "_inject", "_grp",
]


# ─────────────────────────────────────────────────────────────────────────────
#  Internal Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_aov_channels(node):
    """Return sorted list of channel layer names available in the node."""
    layers = set()
    for ch in node.channels():
        layer = ch.split(".")[0]
        if layer not in _EXCLUSION_SET:
            layers.add(layer)
    return sorted(l for l in layers if "crypto" not in l.lower())


def _get_added_aovs(node):
    """Return list of AOV names currently added to the mixer, in knob order."""
    aovs = []
    for k in node.knobs():
        if k.endswith("_tex"):
            aovs.append(k[:-4])
    return aovs


def _autoBackdrop(selNodes):
    """Create a backdrop around the given nodes."""
    if not selNodes:
        return nuke.nodes.BackdropNode()

    for nde in selNodes:
        nde['xpos'].setValue(nde.xpos())
        nde['ypos'].setValue(nde.ypos())

    bdX = min(nde.xpos() for nde in selNodes)
    bdY = min(nde.ypos() for nde in selNodes)
    bdW = max(nde.xpos() + nde.screenWidth() for nde in selNodes) - bdX
    bdH = max(nde.ypos() + nde.screenHeight() for nde in selNodes) - bdY

    margin = 100
    bdX -= margin
    bdY -= margin
    bdW += 2 * margin
    bdH += 2 * margin

    bd = nuke.nodes.BackdropNode(
        xpos=bdX, bdwidth=bdW, ypos=bdY, bdheight=bdH,
        tile_color=1244014335, z_order=-10
    )
    bd['selected'].setValue(False)
    return bd


def _remove_footer_knobs(node):
    """Remove the footer knobs (mix link, mix_div, credit)."""
    for _, knob in list(node.knobs().items()):
        if isinstance(knob, nuke.Link_Knob) and knob.name() == "mix":
            node.removeKnob(knob)
            break
    for kname in ("mix_div", "credit"):
        knob = node.knob(kname)
        if knob:
            node.removeKnob(knob)


def _add_footer_knobs(node):
    """Re-add the footer knobs (mix, divider, credit)."""
    knob = nuke.Link_Knob("mix", "mix")
    knob.setLink("merge_mask.mix")
    node.addKnob(knob)

    node.addKnob(nuke.Text_Knob("mix_div", ""))

    node.addKnob(nuke.Text_Knob(
        "credit", "",
        '<font><br/><b><a href="https://linktr.ee/har8unyan" '
        'style="color:#666">Harut Harutyunyan</a></b></font>'
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Kelvin  →  RGB Conversion
# ─────────────────────────────────────────────────────────────────────────────

def _kelvin_to_rgb_raw(kelvin):
    """Tanner Helland blackbody approximation.  Returns (r, g, b) in 0-1."""
    t = max(1000.0, min(40000.0, float(kelvin))) / 100.0

    # Red
    if t <= 66:
        r = 255.0
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        r = max(0.0, min(255.0, r))

    # Green
    if t <= 66:
        g = 99.4708025861 * math.log(t) - 161.1195681661
    else:
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    g = max(0.0, min(255.0, g))

    # Blue
    if t >= 66:
        b = 255.0
    elif t <= 19:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(t - 10) - 305.0447927307
        b = max(0.0, min(255.0, b))

    return (r / 255.0, g / 255.0, b / 255.0)


def kelvin_to_rgb(kelvin):
    """Convert Kelvin to RGB multiplier, normalised so 6500 K = (1,1,1)."""
    raw = _kelvin_to_rgb_raw(kelvin)
    ref = _kelvin_to_rgb_raw(6500)
    return (
        raw[0] / max(ref[0], 1e-6),
        raw[1] / max(ref[1], 1e-6),
        raw[2] / max(ref[2], 1e-6),
    )


def update_temp_knobs(node, aov_name):
    """Called from knobChanged: convert Kelvin slider to hidden RGB knobs."""
    temp_knob = node.knob(aov_name + "_temp")
    if not temp_knob:
        return
    r, g, b = kelvin_to_rgb(temp_knob.value())
    for val, suffix in [(r, "_tempr"), (g, "_tempg"), (b, "_tempb")]:
        k = node.knob(aov_name + suffix)
        if k:
            k.setValue(val)


# ─────────────────────────────────────────────────────────────────────────────
#  Add / Remove AOV  —  Knobs
# ─────────────────────────────────────────────────────────────────────────────

def remove_aov_knobs(node, aov_name):
    """Remove all UI knobs belonging to a specific AOV."""
    for suffix in _AOV_SUFFIXES:
        knob = node.knob(aov_name + suffix)
        if knob:
            node.removeKnob(knob)


def _add_aov_knobs(node, aov_name, artistic):
    """Add the UI knobs for one AOV.  Does NOT create internal nodes."""

    # ── Header ────────────────────────────────────────────────────────────
    node.addKnob(nuke.Text_Knob(
        aov_name + "_tex", "",
        '<font size=4 color="orange">{}</font>\n'.format(aov_name)
    ))

    k = nuke.String_Knob(aov_name + "_about", "")
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # ── Control buttons ──────────────────────────────────────────────────

    # [S]olo
    k = nuke.Boolean_Knob(
        aov_name + "_solo",
        '<font color="green"><b>[S]</b></font>')
    k.setFlag(nuke.STARTLINE)
    node.addKnob(k)

    # [M]ute
    k = nuke.Boolean_Knob(
        aov_name + "_mute",
        '<font color="red"><b>[M]</b></font>')
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # [D]isable
    k = nuke.Boolean_Knob(
        aov_name + "_dis",
        '<font color="orange"><b>[D]</b></font>')
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # Inject toggle
    k = nuke.Boolean_Knob(aov_name + "_inject", "inject")
    k.setValue(1)
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # [R]eset  (NEW)
    reset_script = (
        "import _LightMixer_utils as _lmu\n"
        "nn = nuke.thisKnob().name().rsplit('_', 1)[0]\n"
        "_lmu.reset_aov(nuke.thisNode(), nn)"
    )
    k = nuke.PyScript_Knob(
        aov_name + "_reset",
        '<font color="cyan"><b>[R]</b></font>',
        reset_script)
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # [V]iew / Preview  (NEW)
    preview_script = (
        "import _LightMixer_utils as _lmu\n"
        "nn = nuke.thisKnob().name().rsplit('_', 1)[0]\n"
        "_lmu.preview_aov(nuke.thisNode(), nn)"
    )
    k = nuke.PyScript_Knob(
        aov_name + "_preview",
        '<font color="white"><b>[V]</b></font>',
        preview_script)
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # Move up  (NEW)
    up_script = (
        "import _LightMixer_utils as _lmu\n"
        "nn = nuke.thisKnob().name().rsplit('_', 1)[0]\n"
        "_lmu.move_aov_up(nuke.thisNode(), nn)"
    )
    k = nuke.PyScript_Knob(aov_name + "_up", u"\u25b2", up_script)
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # Move down  (NEW)
    dn_script = (
        "import _LightMixer_utils as _lmu\n"
        "nn = nuke.thisKnob().name().rsplit('_', 1)[0]\n"
        "_lmu.move_aov_dn(nuke.thisNode(), nn)"
    )
    k = nuke.PyScript_Knob(aov_name + "_dn", u"\u25bc", dn_script)
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # Delete [X]
    del_script = (
        "import _LightMixer_utils as _lmu\n"
        "nn = nuke.thisKnob().name().rsplit('_', 1)[0]\n"
        "_lmu.delete_aov(nuke.thisNode(), nn)"
    )
    k = nuke.PyScript_Knob(aov_name + "_del", "X", del_script)
    k.clearFlag(nuke.STARTLINE)
    node.addKnob(k)

    # ── Parameter knobs ──────────────────────────────────────────────────

    # Color
    k = nuke.Color_Knob(aov_name + "_col", "Color")
    k.setValue(1)
    k.setSingleValue(False)
    node.addKnob(k)

    # Intensity (standard mode only)
    if not artistic:
        k = nuke.Double_Knob(aov_name + "_intens", "Intensity")
        k.setValue(1)
        k.setRange(0, 5)
        node.addKnob(k)

    # Exposure
    k = nuke.Double_Knob(aov_name + "_expo", "Exposure")
    k.setValue(0)
    k.setRange(-5, 5)
    node.addKnob(k)

    # Temperature  (NEW)
    k = nuke.Double_Knob(aov_name + "_temp", "Temperature (K)")
    k.setValue(6500)
    k.setRange(1000, 15000)
    node.addKnob(k)

    # Hidden temperature RGB values  (NEW)
    for suffix in ("_tempr", "_tempg", "_tempb"):
        k = nuke.Double_Knob(aov_name + suffix, "")
        k.setValue(1.0)
        node.addKnob(k)
        k.setVisible(False)

    # Gamma (artistic mode only)
    if artistic:
        k = nuke.Double_Knob(aov_name + "_gam", "Gamma")
        k.setValue(1)
        k.setRange(0.2, 5)
        node.addKnob(k)

        k = nuke.Double_Knob(aov_name + "_sat", "Saturation")
        k.setValue(1)
        k.setRange(0, 1)
        node.addKnob(k)

    # Group assignment  (NEW)
    k = nuke.String_Knob(aov_name + "_grp", "Group")
    k.setValue("")
    node.addKnob(k)

    # Divider
    node.addKnob(nuke.Text_Knob(aov_name + "_div", ""))


# ─────────────────────────────────────────────────────────────────────────────
#  Add / Remove AOV  —  Internal Node Graph
# ─────────────────────────────────────────────────────────────────────────────

def _create_aov_nodes(node, aov_name, artistic):
    """Create the internal node graph for one AOV inside the gizmo."""
    node.begin()

    output = nuke.toNode("Output1")
    merge_mask = nuke.toNode("merge_mask")
    mask = nuke.toNode("mask")
    solo_sw = nuke.toNode("solo_switch")
    inpt = solo_sw.input(0)

    # Shuffle: extract AOV layer
    shuffle = nuke.nodes.Shuffle()
    shuffle["in"].setValue(aov_name)
    shuffle.setInput(0, inpt)
    shuffle.setXYpos(inpt.xpos() - 150, inpt.ypos() + 220)

    # Merge(from): subtract original AOV from main stream
    m_from = nuke.nodes.Merge2(operation="from", output="rgb", bbox="B")
    m_from.setInput(0, inpt)
    m_from.setInput(1, shuffle)
    m_from.setXYpos(inpt.xpos(), shuffle.ypos())

    # Merge(plus): add modified AOV back
    m_plus = nuke.nodes.Merge2(operation="plus", output="rgb", bbox="B")

    # ShuffleCopy: write modified values back to AOV layer
    shuffle_copy = nuke.nodes.ShuffleCopy(out=aov_name)
    shuffle_copy["in"].setValue("rgb")
    shuffle_copy["red"].setValue("red")
    shuffle_copy["green"].setValue("green")
    shuffle_copy["blue"].setValue("blue")
    shuffle_copy["alpha"].setValue("black")
    shuffle_copy.setInput(0, m_from)
    shuffle_copy.setXYpos(inpt.xpos(), m_from.ypos() + 100)
    shuffle_copy["disable"].setExpression(
        "1-{}_inject".format(aov_name))

    m_plus.setInput(0, shuffle_copy)
    m_plus.setXYpos(inpt.xpos(), m_from.ypos() + 130)
    m_plus["disable"].setExpression("{}_mute".format(aov_name))

    # ── Colour processing chain ──────────────────────────────────────────

    if artistic:
        color_n = nuke.nodes.Grade()
        color_n["white"].setSingleValue(False)
        color_n["white"].setExpression(
            "parent.{}_col.r".format(aov_name), channel=0)
        color_n["white"].setExpression(
            "parent.{}_col.g".format(aov_name), channel=1)
        color_n["white"].setExpression(
            "parent.{}_col.b".format(aov_name), channel=2)
        color_n["multiply"].setExpression(
            "pow(2, {}_expo)".format(aov_name))
        color_n["gamma"].setExpression("{}_gam".format(aov_name))
        color_n.setInput(0, shuffle)
        color_n.setXYpos(shuffle.xpos(), shuffle.ypos() + 50)
    else:
        color_n = nuke.nodes.Multiply(channels="rgb")
        color_n["value"].setSingleValue(False)
        color_n.setName("color")
        color_n["value"].setExpression(
            "parent.{}_col.r".format(aov_name), channel=0)
        color_n["value"].setExpression(
            "parent.{}_col.g".format(aov_name), channel=1)
        color_n["value"].setExpression(
            "parent.{}_col.b".format(aov_name), channel=2)
        color_n.setInput(0, shuffle)
        color_n.setXYpos(shuffle.xpos(), shuffle.ypos() + 50)

    # Temperature Grade  (NEW) — between colour and intensity
    temp_n = nuke.nodes.Grade()
    temp_n.setName("{}_temp_grade".format(aov_name))
    temp_n["white"].setSingleValue(False)
    temp_n["white"].setExpression(
        "parent.{}_tempr".format(aov_name), channel=0)
    temp_n["white"].setExpression(
        "parent.{}_tempg".format(aov_name), channel=1)
    temp_n["white"].setExpression(
        "parent.{}_tempb".format(aov_name), channel=2)
    temp_n.setInput(0, color_n)
    temp_n.setXYpos(color_n.xpos(), color_n.ypos() + 50)
    temp_n["disable"].setExpression("{}_dis".format(aov_name))

    # Final intensity / saturation node  (named {}_mult for solo reference)
    if artistic:
        mult_n = nuke.nodes.Saturation()
        mult_n.setName("{}_mult".format(aov_name))
        mult_n["saturation"].setExpression("{}_sat".format(aov_name))
        mult_n.setInput(0, temp_n)
        mult_n.setXYpos(temp_n.xpos(), temp_n.ypos() + 50)
    else:
        mult_n = nuke.nodes.Multiply(channels="rgb")
        mult_n.setName("{}_mult".format(aov_name))
        mult_n["value"].setExpression(
            "pow(2, {0}_expo) * {0}_intens".format(aov_name))
        mult_n.setInput(0, temp_n)
        mult_n.setXYpos(temp_n.xpos(), temp_n.ypos() + 50)

    color_n["disable"].setExpression("{}_dis".format(aov_name))
    mult_n["disable"].setExpression("{}_dis".format(aov_name))

    # Connect to main stream
    shuffle_copy.setInput(1, mult_n)
    m_plus.setInput(1, mult_n)

    # Reconnect chain
    solo_sw.setInput(0, m_plus)
    solo_sw.setXYpos(inpt.xpos() + 150, m_plus.ypos() + 220)
    merge_mask.setXYpos(solo_sw.xpos(), m_plus.ypos() + 250)
    mask.setXYpos(solo_sw.xpos() + 150, m_plus.ypos() + 250)
    output.setXYpos(inpt.xpos(), m_plus.ypos() + 280)

    # Backdrop
    bdrp = _autoBackdrop(
        [shuffle, color_n, temp_n, mult_n, m_from, m_plus, shuffle_copy])
    bdrp.setName("__{}__".format(aov_name))

    node.end()


def add_aov_internal(node, aov_name, artistic):
    """Add a single AOV to the mixer: creates knobs and internal nodes."""
    if node.knob(aov_name + "_tex"):
        return  # already added

    _remove_footer_knobs(node)
    _add_aov_knobs(node, aov_name, artistic)
    _add_footer_knobs(node)
    _create_aov_nodes(node, aov_name, artistic)
    update_temp_knobs(node, aov_name)


def delete_aov(node, aov_name):
    """Delete an AOV: remove internal nodes and UI knobs."""
    node.begin()
    bdrp = nuke.toNode("__{}__".format(aov_name))
    if bdrp:
        for nd in bdrp.getNodes() + [bdrp]:
            nuke.delete(nd)
    node.end()
    remove_aov_knobs(node, aov_name)


# ─────────────────────────────────────────────────────────────────────────────
#  Select AOV  (dialog — replaces inline gizmo script)
# ─────────────────────────────────────────────────────────────────────────────

def select_aov(node):
    """Show dialog to select and add AOV(s)."""
    aov_list = _get_aov_channels(node)

    class ChooseAov(nukescripts.PythonPanel):
        def __init__(self):
            super(ChooseAov, self).__init__('Select AOV')
            self.setMinimumSize(300, 80)
            self.aov_name = nuke.Enumeration_Knob(
                "aov_name", "AOV Name: ", ["_SEARCH_"] + aov_list)
            self.artistic_control = nuke.Boolean_Knob(
                "artistic", "Artistic Control")
            self.artistic_control.clearFlag(nuke.STARTLINE)
            self.addKnob(self.aov_name)
            self.addKnob(self.artistic_control)

            self.addKnob(nuke.Text_Knob("div", ""))
            self.search_where = nuke.Radio_Knob(
                "search_where", "", ("starts", "ends", "contains"))
            self.search_where.setFlag(nuke.STARTLINE)
            self.addKnob(self.search_where)

            self.search_for = nuke.String_Knob("search_for", "", "lgt_")
            self.addKnob(self.search_for)
            self.search_for.clearFlag(nuke.STARTLINE)
            self.div1 = nuke.Text_Knob("div1", "")
            self.addKnob(self.div1)

        def knobChanged(self, knob):
            if knob.name() == "aov_name":
                visible = knob.value() == "_SEARCH_"
                self.search_where.setVisible(visible)
                self.search_for.setVisible(visible)
                self.div1.setVisible(visible)

    panel = ChooseAov()
    if panel.showModalDialog():
        name = panel.aov_name.value()
        artistic = panel.artistic_control.value()

        if name == "_SEARCH_":
            search_where = panel.search_where.value()
            search_for = panel.search_for.value().lower()
            if search_where == "starts":
                aov_names = [l for l in aov_list
                             if l.lower().startswith(search_for)]
            elif search_where == "ends":
                aov_names = [l for l in aov_list
                             if l.lower().endswith(search_for)]
            elif search_where == "contains":
                aov_names = [l for l in aov_list
                             if search_for in l.lower()]
            else:
                aov_names = []
        else:
            aov_names = [name]

        for aov_name in aov_names:
            add_aov_internal(node, aov_name, artistic)


# ─────────────────────────────────────────────────────────────────────────────
#  Auto-Detect Light AOVs
# ─────────────────────────────────────────────────────────────────────────────

def auto_detect_aovs(node):
    """Auto-detect and batch-add all light-related AOVs."""
    all_aovs = _get_aov_channels(node)
    if not all_aovs:
        nuke.message(
            "No channels found.\n"
            "Connect an input with multi-channel EXR data.")
        return

    existing = set(_get_added_aovs(node))

    light_aovs = []
    for aov in all_aovs:
        if aov in existing:
            continue
        aov_lower = aov.lower()

        is_light = False
        for prefix in _LIGHT_PREFIXES:
            if aov_lower.startswith(prefix.lower()):
                is_light = True
                break
        if not is_light:
            for keyword in _LIGHT_KEYWORDS:
                if keyword in aov_lower:
                    is_light = True
                    break
        if is_light:
            light_aovs.append(aov)

    if not light_aovs:
        remaining = [a for a in all_aovs if a not in existing]
        if not remaining:
            nuke.message("All available AOVs have already been added.")
            return
        msg = ("No light AOVs detected by naming convention.\n\n"
               "Available AOVs:\n" + "\n".join(remaining) +
               "\n\nWould you like to add ALL remaining AOVs?")
        if not nuke.ask(msg):
            return
        light_aovs = remaining
    else:
        msg = ("Found {} light AOV(s):\n\n{}\n\nAdd all?".format(
            len(light_aovs), "\n".join(light_aovs)))
        if not nuke.ask(msg):
            return

    artistic = nuke.ask(
        "Use Artistic Controls?\n"
        "(Adds Gamma and Saturation per light)\n\n"
        "Yes = Artistic  |  No = Standard")

    for aov_name in light_aovs:
        add_aov_internal(node, aov_name, artistic)

    nuke.message("Added {} light AOV(s).".format(len(light_aovs)))


# ─────────────────────────────────────────────────────────────────────────────
#  Preset System
# ─────────────────────────────────────────────────────────────────────────────

def save_preset(node):
    """Save the current light mix as a named JSON preset."""
    aovs = _get_added_aovs(node)
    if not aovs:
        nuke.message("No AOVs added to save.")
        return

    if not os.path.isdir(_PRESET_DIR):
        os.makedirs(_PRESET_DIR)

    name = nuke.getInput("Preset name:", "my_preset")
    if not name or not name.strip():
        return
    name = name.strip().replace(" ", "_")

    preset = {"aovs": {}}
    for aov in aovs:
        aov_data = {"artistic": node.knob(aov + "_gam") is not None}
        for suffix in _VALUE_SUFFIXES:
            knob = node.knob(aov + suffix)
            if knob:
                if isinstance(knob, nuke.Color_Knob):
                    aov_data[suffix] = [knob.value(i) for i in range(3)]
                elif isinstance(knob, nuke.String_Knob):
                    aov_data[suffix] = knob.value()
                else:
                    aov_data[suffix] = knob.value()
        preset["aovs"][aov] = aov_data

    filepath = os.path.join(_PRESET_DIR, name + ".json")
    with open(filepath, "w") as f:
        json.dump(preset, f, indent=2)
    nuke.message("Preset saved: {}".format(name))


def load_preset(node):
    """Load a preset and apply values."""
    if not os.path.isdir(_PRESET_DIR):
        nuke.message("No presets directory found.")
        return

    presets = sorted(
        f[:-5] for f in os.listdir(_PRESET_DIR) if f.endswith(".json"))
    if not presets:
        nuke.message("No presets found.")
        return

    panel = nuke.Panel("Load Preset")
    panel.addEnumerationPulldown("Preset", " ".join(presets))
    if not panel.show():
        return

    name = panel.value("Preset")
    filepath = os.path.join(_PRESET_DIR, name + ".json")

    try:
        with open(filepath, "r") as f:
            preset = json.load(f)
    except Exception as e:
        nuke.message("Error reading preset: {}".format(e))
        return

    try:
        nuke.Undo.begin("Load LightMixer Preset: {}".format(name))
    except Exception:
        pass

    try:
        existing = set(_get_added_aovs(node))
        for aov_name, aov_data in preset.get("aovs", {}).items():
            if aov_name not in existing:
                artistic = aov_data.get("artistic", False)
                add_aov_internal(node, aov_name, artistic)

            for suffix, value in aov_data.items():
                if suffix.startswith("_"):
                    knob = node.knob(aov_name + suffix)
                    if knob:
                        try:
                            if isinstance(value, list):
                                for i, v in enumerate(value):
                                    knob.setValue(v, i)
                            else:
                                knob.setValue(value)
                        except Exception:
                            pass
            update_temp_knobs(node, aov_name)
    except Exception as e:
        nuke.message("Error applying preset: {}".format(e))
    finally:
        try:
            nuke.Undo.end()
        except Exception:
            pass

    nuke.message("Preset loaded: {}".format(name))


def delete_preset(node):
    """Delete a saved preset file."""
    if not os.path.isdir(_PRESET_DIR):
        nuke.message("No presets found.")
        return

    presets = sorted(
        f[:-5] for f in os.listdir(_PRESET_DIR) if f.endswith(".json"))
    if not presets:
        nuke.message("No presets found.")
        return

    panel = nuke.Panel("Delete Preset")
    panel.addEnumerationPulldown("Preset", " ".join(presets))
    if not panel.show():
        return

    name = panel.value("Preset")
    filepath = os.path.join(_PRESET_DIR, name + ".json")

    if nuke.ask("Delete preset '{}'?".format(name)):
        try:
            os.remove(filepath)
            nuke.message("Preset deleted: {}".format(name))
        except Exception as e:
            nuke.message("Error deleting preset: {}".format(e))


# ─────────────────────────────────────────────────────────────────────────────
#  Reset Per Light
# ─────────────────────────────────────────────────────────────────────────────

def reset_aov(node, aov_name):
    """Reset a single AOV's parameters to defaults.  Supports undo."""
    try:
        nuke.Undo.begin("Reset LightMixer: {}".format(aov_name))
    except Exception:
        pass

    try:
        defaults = {
            "_col": [1.0, 1.0, 1.0],
            "_intens": 1.0,
            "_expo": 0.0,
            "_temp": 6500.0,
            "_gam": 1.0,
            "_sat": 1.0,
            "_mute": False,
            "_solo": False,
            "_dis": False,
            "_inject": True,
        }
        for suffix, value in defaults.items():
            knob = node.knob(aov_name + suffix)
            if knob:
                if isinstance(value, list):
                    for i, v in enumerate(value):
                        knob.setValue(v, i)
                else:
                    knob.setValue(value)

        update_temp_knobs(node, aov_name)
    finally:
        try:
            nuke.Undo.end()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  Light Preview
# ─────────────────────────────────────────────────────────────────────────────

def preview_aov(node, aov_name):
    """Toggle solo on an AOV and view in the active Viewer."""
    solo_knob = node.knob(aov_name + "_solo")
    if solo_knob:
        solo_knob.setValue(not solo_knob.value())

    try:
        viewer = nuke.activeViewer()
        if viewer:
            vnode = viewer.node()
            vnode.setInput(vnode.activeInput() or 0, node)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  AOV Reordering
# ─────────────────────────────────────────────────────────────────────────────

def _save_aov_values(node, aov_name):
    """Save all knob values for an AOV."""
    data = {
        "artistic": node.knob(aov_name + "_gam") is not None,
        "values": {},
    }
    for suffix in _VALUE_SUFFIXES:
        knob = node.knob(aov_name + suffix)
        if knob:
            if isinstance(knob, nuke.Color_Knob):
                data["values"][suffix] = [knob.value(i) for i in range(3)]
            elif isinstance(knob, nuke.String_Knob):
                data["values"][suffix] = knob.value()
            else:
                data["values"][suffix] = knob.value()
    return data


def _restore_aov_values(node, aov_name, data):
    """Restore saved knob values for an AOV."""
    for suffix, value in data.get("values", {}).items():
        knob = node.knob(aov_name + suffix)
        if knob:
            try:
                if isinstance(value, list):
                    for i, v in enumerate(value):
                        knob.setValue(v, i)
                else:
                    knob.setValue(value)
            except Exception:
                pass
    update_temp_knobs(node, aov_name)


def _reorder_aovs(node, aovs, idx_a, idx_b):
    """Swap two AOVs and rebuild the knob order."""
    try:
        nuke.Undo.begin("Reorder LightMixer AOVs")
    except Exception:
        pass

    try:
        # Save all AOV data
        all_data = {}
        for aov in aovs:
            all_data[aov] = _save_aov_values(node, aov)

        # Remove all AOV knobs
        for aov in aovs:
            remove_aov_knobs(node, aov)

        # Remove footer
        _remove_footer_knobs(node)

        # Swap order
        aovs[idx_a], aovs[idx_b] = aovs[idx_b], aovs[idx_a]

        # Re-add knobs in new order
        for aov in aovs:
            data = all_data[aov]
            _add_aov_knobs(node, aov, data["artistic"])
            _restore_aov_values(node, aov, data)

        # Re-add footer
        _add_footer_knobs(node)
    finally:
        try:
            nuke.Undo.end()
        except Exception:
            pass


def move_aov_up(node, aov_name):
    """Move an AOV up one position in the properties panel."""
    aovs = _get_added_aovs(node)
    if aov_name not in aovs:
        return
    idx = aovs.index(aov_name)
    if idx == 0:
        return
    _reorder_aovs(node, aovs, idx, idx - 1)


def move_aov_dn(node, aov_name):
    """Move an AOV down one position in the properties panel."""
    aovs = _get_added_aovs(node)
    if aov_name not in aovs:
        return
    idx = aovs.index(aov_name)
    if idx >= len(aovs) - 1:
        return
    _reorder_aovs(node, aovs, idx, idx + 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Contact Sheet
# ─────────────────────────────────────────────────────────────────────────────

def generate_contact_sheet(node):
    """Create a ContactSheet node showing all added AOVs side by side."""
    aovs = _get_added_aovs(node)
    if not aovs:
        nuke.message("No AOVs added yet.")
        return

    input_node = node.input(0)
    if not input_node:
        nuke.message("No input connected to LightMixer.")
        return

    base_x = node.xpos() + 200
    base_y = node.ypos()
    shuffle_nodes = []

    for i, aov_name in enumerate(aovs):
        s = nuke.nodes.Shuffle()
        s["in"].setValue(aov_name)
        s.setInput(0, input_node)
        s["label"].setValue(aov_name)
        s.setXYpos(base_x + i * 110, base_y)
        shuffle_nodes.append(s)

    num_cols = min(4, len(aovs))
    num_rows = int(math.ceil(len(aovs) / float(num_cols)))

    try:
        w = input_node.width()
        h = input_node.height()
    except Exception:
        w, h = 1920, 1080

    cs = nuke.nodes.ContactSheet()
    cs["rows"].setValue(num_rows)
    cs["columns"].setValue(num_cols)
    cs["width"].setValue(w * num_cols)
    cs["height"].setValue(h * num_rows)

    for i, s in enumerate(shuffle_nodes):
        cs.setInput(i, s)

    cs["label"].setValue("LightMixer Contact Sheet")
    cs.setXYpos(base_x + len(aovs) * 55 - 50, base_y + 120)

    for n in nuke.allNodes():
        n["selected"].setValue(False)
    cs["selected"].setValue(True)
    nuke.show(cs)


# ─────────────────────────────────────────────────────────────────────────────
#  Group Actions
# ─────────────────────────────────────────────────────────────────────────────

def group_actions(node):
    """Show panel for group-level operations."""
    aovs = _get_added_aovs(node)
    if not aovs:
        nuke.message("No AOVs added.")
        return

    groups = {}
    for aov in aovs:
        grp_knob = node.knob(aov + "_grp")
        if grp_knob:
            grp = grp_knob.value().strip()
            if grp:
                groups.setdefault(grp, []).append(aov)

    if not groups:
        nuke.message(
            "No groups defined.\n\n"
            "Assign groups using the 'Group' field on each light AOV.")
        return

    group_names = sorted(groups.keys())

    panel = nuke.Panel("Group Actions")
    panel.addEnumerationPulldown("Group", " ".join(group_names))
    panel.addEnumerationPulldown(
        "Action",
        "Solo_Group Mute_Group Unsolo_All Unmute_All Reset_Group")
    if not panel.show():
        return

    group = panel.value("Group")
    action = panel.value("Action")
    members = groups.get(group, [])

    try:
        nuke.Undo.begin("LightMixer Group: {} {}".format(action, group))
    except Exception:
        pass

    try:
        member_set = set(members)
        if action == "Solo_Group":
            for aov in aovs:
                k = node.knob(aov + "_solo")
                if k:
                    k.setValue(aov in member_set)
        elif action == "Mute_Group":
            for aov in members:
                k = node.knob(aov + "_mute")
                if k:
                    k.setValue(True)
        elif action == "Unsolo_All":
            for aov in aovs:
                k = node.knob(aov + "_solo")
                if k:
                    k.setValue(False)
        elif action == "Unmute_All":
            for aov in aovs:
                k = node.knob(aov + "_mute")
                if k:
                    k.setValue(False)
        elif action == "Reset_Group":
            for aov in members:
                reset_aov(node, aov)
    finally:
        try:
            nuke.Undo.end()
        except Exception:
            pass
