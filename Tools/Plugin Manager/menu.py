import nuke
import os
import re
import shutil
import importlib
import nukescripts

# -----------------------------------------------------------------------------
#  My Gizmos + My Tools - Auto-building Menus
# -----------------------------------------------------------------------------

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_GIZMO_DIR = os.path.join(_PLUGIN_DIR, "My_Gizmos")
_TOOLS_DIR = os.path.join(_PLUGIN_DIR, "My_Tools")

# -- Helpers -------------------------------------------------------------------

def _pretty(name):
    return re.sub(r"[_\-]+", " ", name).title()


def _module_name(filepath, base_dir):
    rel = os.path.relpath(filepath, base_dir)
    rel = os.path.splitext(rel)[0]
    return rel.replace(os.sep, ".")


def _sub_folders(base):
    result = []
    for root, dirs, _ in os.walk(base):
        dirs[:] = [d for d in sorted(dirs) if not d.startswith((".", "_"))]
        for d in dirs:
            result.append(os.path.join(root, d))
    return result


# -- Per-file command builders -------------------------------------------------

def _add_py_cmd(menu, filepath, base_dir):
    mod_name = _module_name(filepath, base_dir)
    label    = _pretty(os.path.splitext(os.path.basename(filepath))[0])
    def _cmd(m=mod_name):
        mod = importlib.import_module(m)
        importlib.reload(mod)
        mod.run()
    menu.addCommand(label, _cmd)


def _add_nk_cmd(menu, filepath):
    label = _pretty(os.path.splitext(os.path.basename(filepath))[0])
    menu.addCommand(label, lambda f=filepath: nuke.nodePaste(f))


# -- Recursive menu builder ----------------------------------------------------

def _build_menu(parent_menu, folder, base_dir, py_handler):
    try:
        entries = sorted(os.listdir(folder))
    except OSError:
        return

    for entry in entries:
        fp = os.path.join(folder, entry)
        if os.path.isdir(fp) and not entry.startswith((".", "_")):
            _build_menu(parent_menu.addMenu(_pretty(entry)), fp, base_dir, py_handler)

    for entry in entries:
        fp  = os.path.join(folder, entry)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(entry)[1].lower()

        if ext == ".gizmo":
            name  = os.path.splitext(entry)[0]
            label = _pretty(name)
            parent_menu.addCommand(label, lambda n=name: nuke.createNode(n))

        elif ext == ".nk" and not entry.startswith((".", "_")):
            _add_nk_cmd(parent_menu, fp)

        elif ext == ".py" and not entry.startswith((".", "_")):
            py_handler(parent_menu, fp, base_dir)


# -- Refresh -------------------------------------------------------------------

def refresh_menus():
    nodes_tb = nuke.menu("Nodes")
    old_gizmos = nodes_tb.findItem("My Gizmos")
    if old_gizmos:
        nodes_tb.removeItem("My Gizmos")

    nuke.pluginAddPath(_GIZMO_DIR)
    for fp in _sub_folders(_GIZMO_DIR):
        nuke.pluginAddPath(fp)

    new_gizmos = nodes_tb.addMenu("My Gizmos", icon="my_menu_icon.png")
    _build_menu(new_gizmos, _GIZMO_DIR, _GIZMO_DIR, _add_py_cmd)

    menubar  = nuke.menu("Nuke")
    old_tools = menubar.findItem("My Tools")
    if old_tools:
        menubar.removeItem("My Tools")

    nuke.pluginAddPath(_TOOLS_DIR)
    for fp in _sub_folders(_TOOLS_DIR):
        nuke.pluginAddPath(fp)

    new_tools = menubar.addMenu("My Tools", icon="my_menu_icon.png")
    _build_menu(new_tools, _TOOLS_DIR, _TOOLS_DIR, _add_py_cmd)
    _append_utility_items(new_tools)

    g_total = sum(
        len([f for f in files if os.path.splitext(f)[1].lower() in (".gizmo", ".py", ".nk")])
        for _, _, files in os.walk(_GIZMO_DIR)
    )
    t_total = sum(
        len([f for f in files if f.lower().endswith(".py") and not f.startswith((".", "_"))])
        for _, _, files in os.walk(_TOOLS_DIR)
    )
    nuke.message(
        "Menus refreshed!\n\n"
        "  My Gizmos -> {} item(s)\n"
        "  My Tools  -> {} script(s)".format(g_total, t_total)
    )
    print("[My Tools] Refresh complete - {} gizmos, {} tools.".format(g_total, t_total))


# -- Install -------------------------------------------------------------------

def _collect_sub_folders(base):
    result = []
    for root, dirs, _ in os.walk(base):
        dirs[:] = [d for d in sorted(dirs) if not d.startswith((".", "_"))]
        for d in dirs:
            fp      = os.path.join(root, d)
            rel     = os.path.relpath(fp, base)
            result.append((rel.replace(os.sep, " / "), fp))
    return result


def Install_dialog():
    gizmo_folders = _collect_sub_folders(_GIZMO_DIR)
    tools_folders = _collect_sub_folders(_TOOLS_DIR)

    gizmo_labels = [label for label, _ in gizmo_folders]
    tools_labels = [label for label, _ in tools_folders]

    dest_labels = (
        ["-- My Gizmos --"] + ["  Gizmos / {}".format(l) for l in gizmo_labels] +
        ["-- My Tools --"]  + ["  Tools  / {}".format(l) for l in tools_labels]
    )

    class InstallPanel(nukescripts.PythonPanel):
        def __init__(self):
            super(InstallPanel, self).__init__("Install to My Gizmos / My Tools")

            self.pub_type = nuke.Enumeration_Knob("pub_type", "Install type", [
                "Selected nodes as .nk",
                "Selected nodes as .gizmo",
                "Copy a .py script"
            ])
            self.name_knob = nuke.String_Knob("name", "Name")
            self.name_knob.setValue("my_snippet")

            self.dest = nuke.Enumeration_Knob("dest", "Destination", dest_labels)

            self.custom_folder = nuke.String_Knob("custom_folder", "New sub-folder")
            self.custom_folder.setTooltip(
                "Optional: Type a new folder name to create it inside the selected destination.")

            self.refresh = nuke.Boolean_Knob("refresh", "Refresh menus after Installing")
            self.refresh.setValue(True)
            self.refresh.setFlag(nuke.STARTLINE)

            self.addKnob(self.pub_type)
            self.addKnob(self.name_knob)
            self.addKnob(self.dest)
            self.addKnob(self.custom_folder)
            self.addKnob(self.refresh)

    p = InstallPanel()
    if not p.showModalDialog():
        return

    pub_type    = p.pub_type.value()
    name        = p.name_knob.value().strip().replace(" ", "_")
    dest_label  = p.dest.value().strip()
    custom_sub  = p.custom_folder.value().strip()
    do_refresh  = p.refresh.value()

    if not name:
        nuke.message("Please enter a name for the Installed item.")
        return

    dest_folder = None

    if dest_label.startswith("Gizmos /"):
        inner = dest_label.replace("Gizmos /", "").strip()
        for label, path in gizmo_folders:
            if label == inner:
                dest_folder = path
                break

    elif dest_label.startswith("Tools  /"):
        inner = dest_label.replace("Tools  /", "").strip()
        for label, path in tools_folders:
            if label == inner:
                dest_folder = path
                break

    if dest_folder is None:
        if "Tools" in dest_label:
            dest_folder = _TOOLS_DIR
        else:
            dest_folder = _GIZMO_DIR

    if custom_sub:
        dest_folder = os.path.join(dest_folder, custom_sub.replace(" ", "_"))

    os.makedirs(dest_folder, exist_ok=True)

    if pub_type == "Selected nodes as .nk":
        selected = nuke.selectedNodes()
        if not selected:
            nuke.message("No nodes selected. Please select the nodes you want to Install.")
            return
        out_path = os.path.join(dest_folder, name + ".nk")
        nuke.nodeCopy(out_path)
        nuke.message("Installed snippet:\n{}".format(out_path))

    elif pub_type == "Selected nodes as .gizmo":
        selected = nuke.selectedNodes()
        if len(selected) != 1 or selected[0].Class() != "Gizmo":
            if not selected:
                nuke.message("No nodes selected.")
                return
            out_path = os.path.join(dest_folder, name + ".gizmo")
            nuke.nodeCopy(out_path)
        else:
            out_path = os.path.join(dest_folder, name + ".gizmo")
            nuke.nodeCopy(out_path)
        nuke.pluginAddPath(dest_folder)
        nuke.message("Installed gizmo:\n{}".format(out_path))

    elif pub_type == "Copy a .py script":
        src = nuke.getFilename("Select the .py script to Install", "*.py")
        if not src or not os.path.isfile(src):
            nuke.message("No valid file selected.")
            return
        out_path = os.path.join(dest_folder, name + ".py")
        shutil.copy2(src, out_path)
        nuke.message("Installed script:\n{}".format(out_path))

    if do_refresh:
        refresh_menus()


# -- Drag & Drop Install ------------------------------------------------------

def _sanitize_drop_path(text):
    path = text.strip()
    if path.startswith("file:///"):
        path = path[len("file:///"):]
    elif path.startswith("file://"):
        path = path[len("file://"):]
    try:
        import urllib.parse
        path = urllib.parse.unquote(path)
    except ImportError:
        import urllib
        path = urllib.unquote(path)
    path = os.path.normpath(path)
    return path


# -- Batch drop state ----------------------------------------------------------
_drop_queue = []
_drop_timer = None


def _flush_drop_queue():
    global _drop_queue
    files = list(_drop_queue)
    _drop_queue = []
    if not files:
        return
    _drop_install_dialog(files)


def _drop_install_dialog(file_paths):
    is_batch = len(file_paths) > 1

    gizmo_files = [f for f in file_paths if os.path.splitext(f)[1].lower() == ".gizmo"]
    py_files    = [f for f in file_paths if os.path.splitext(f)[1].lower() == ".py"]

    if is_batch:
        lines = []
        for fp in file_paths:
            lines.append("  * {}".format(os.path.basename(fp)))
        file_summary = "<br>".join(lines)
        counts = []
        if gizmo_files:
            counts.append("{} gizmo(s)".format(len(gizmo_files)))
        if py_files:
            counts.append("{} script(s)".format(len(py_files)))
        info_html = '<b>{} files</b>  ({})<br>{}'.format(
            len(file_paths), ", ".join(counts), file_summary)
    else:
        basename = os.path.basename(file_paths[0])
        ext = os.path.splitext(basename)[1].lower()
        info_html = '<b>File:</b>  {}<br><b>Type:</b>  {}'.format(basename, ext)

    if len(py_files) > len(gizmo_files):
        default_root = _TOOLS_DIR
        root_label   = "My Tools"
        target_order = ["My Tools", "My Gizmos"]
    else:
        default_root = _GIZMO_DIR
        root_label   = "My Gizmos"
        target_order = ["My Gizmos", "My Tools"]

    sub_folders = _collect_sub_folders(default_root)
    folder_labels = [root_label + "  (root)"] + [
        "  {} / {}".format(root_label, label) for label, _ in sub_folders
    ]

    class DropInstallPanel(nukescripts.PythonPanel):
        def __init__(self):
            title = "Install Dropped Plugins" if is_batch else "Install Dropped Plugin"
            super(DropInstallPanel, self).__init__(title)

            self.info = nuke.Text_Knob("info", "", info_html)
            self.divider1 = nuke.Text_Knob("div1", "")

            self.name_knob = None
            if not is_batch:
                name_no_ext = os.path.splitext(os.path.basename(file_paths[0]))[0]
                self.name_knob = nuke.String_Knob("name", "Install as")
                self.name_knob.setValue(name_no_ext)

            self.target = nuke.Enumeration_Knob("target", "Target", target_order)

            self.search = nuke.String_Knob("search", "Filter")
            self.search.setTooltip("Type to filter the folder list.")

            self._all_labels = list(folder_labels)
            self.dest = nuke.Enumeration_Knob("dest", "Folder", folder_labels)

            self.custom_folder = nuke.String_Knob("custom_folder", "New sub-folder")
            self.custom_folder.setTooltip(
                "Optional: create a new folder inside the selected destination.")

            self.refresh = nuke.Boolean_Knob("refresh", "Refresh menus after install")
            self.refresh.setValue(True)
            self.refresh.setFlag(nuke.STARTLINE)

            knobs = [self.info, self.divider1]
            if self.name_knob:
                knobs.append(self.name_knob)
            knobs += [self.target, self.search, self.dest,
                      self.custom_folder, self.refresh]
            for k in knobs:
                self.addKnob(k)

        def _apply_filter(self):
            query = self.search.value().strip().lower()
            if not query:
                filtered = list(self._all_labels)
            else:
                filtered = [
                    l for l in self._all_labels
                    if "(root)" in l or query in l.lower()
                ]
            if not filtered:
                filtered = [self._all_labels[0]]
            self.dest.setValues(filtered)

        def knobChanged(self, knob):
            if knob is self.target:
                sel = self.target.value()
                if sel == "My Tools":
                    new_root = _TOOLS_DIR
                else:
                    new_root = _GIZMO_DIR
                new_subs = _collect_sub_folders(new_root)
                self._all_labels = [sel + "  (root)"] + [
                    "  {} / {}".format(sel, l) for l, _ in new_subs
                ]
                self.search.setValue("")
                self.dest.setValues(self._all_labels)

            elif knob is self.search:
                self._apply_filter()

    panel = DropInstallPanel()
    if not panel.showModalDialog():
        return

    target_val  = panel.target.value()
    dest_label  = panel.dest.value().strip()
    custom_sub  = panel.custom_folder.value().strip()
    do_refresh  = panel.refresh.value()

    rename = None
    if panel.name_knob:
        rename = panel.name_knob.value().strip().replace(" ", "_")
        if not rename:
            nuke.message("Please enter a name.")
            return

    if target_val == "My Tools":
        base_root = _TOOLS_DIR
    else:
        base_root = _GIZMO_DIR

    dest_folder = base_root
    if "/" in dest_label:
        inner = dest_label.split("/", 1)[1].strip()
        all_subs = _collect_sub_folders(base_root)
        for label, path in all_subs:
            if label == inner:
                dest_folder = path
                break

    if custom_sub:
        dest_folder = os.path.join(dest_folder, custom_sub.replace(" ", "_"))

    os.makedirs(dest_folder, exist_ok=True)

    installed = []
    skipped   = []

    for fp in file_paths:
        src_base = os.path.basename(fp)
        src_name, src_ext = os.path.splitext(src_base)
        src_ext = src_ext.lower()

        if rename and not is_batch:
            out_name = rename + src_ext
        else:
            out_name = src_name + src_ext

        out_path = os.path.join(dest_folder, out_name)

        if os.path.exists(out_path):
            if not nuke.ask("'{}' already exists in:\n{}\n\nOverwrite?".format(
                    out_name, dest_folder)):
                skipped.append(out_name)
                continue

        shutil.copy2(fp, out_path)

        if src_ext == ".gizmo":
            nuke.pluginAddPath(dest_folder)

        installed.append(out_name)
        print("[Plugin Manager] Drag-install: {}  ->  {}".format(fp, out_path))

    msg_parts = []
    if installed:
        msg_parts.append("Installed {} file(s) to:\n  {}\n".format(
            len(installed), dest_folder))
        for name in installed:
            msg_parts.append("  + {}".format(name))
    if skipped:
        msg_parts.append("\nSkipped {} file(s):".format(len(skipped)))
        for name in skipped:
            msg_parts.append("  - {}".format(name))
    if not installed and not skipped:
        msg_parts.append("Nothing was installed.")

    nuke.message("\n".join(msg_parts))

    if do_refresh and installed:
        refresh_menus()


def _drop_data_handler(mime_type, text):
    global _drop_timer

    if mime_type != "text/plain":
        return None

    path = _sanitize_drop_path(text)

    ext = os.path.splitext(path)[1].lower()
    if ext not in (".gizmo", ".py"):
        return None

    if not os.path.isfile(path):
        return None

    try:
        from PySide2.QtCore import QTimer
    except ImportError:
        from PySide6.QtCore import QTimer

    if path not in _drop_queue:
        _drop_queue.append(path)

    if _drop_timer is not None:
        _drop_timer.stop()

    _drop_timer = QTimer()
    _drop_timer.setSingleShot(True)
    _drop_timer.timeout.connect(_flush_drop_queue)
    _drop_timer.start(300)

    return True


# -- Utility items appended to My Tools ----------------------------------------

def _append_utility_items(menu):
    menu.addSeparator()
    menu.addCommand("Refresh Menus",  refresh_menus)
    menu.addCommand("Install...",     Install_dialog)


# -- Entry points --------------------------------------------------------------

def build_gizmos_menu():
    toolbar = nuke.menu("Nodes")
    gm      = toolbar.addMenu("My Gizmos", icon="my_menu_icon.png")
    _build_menu(gm, _GIZMO_DIR, _GIZMO_DIR, _add_py_cmd)

    total = sum(
        len([f for f in files if os.path.splitext(f)[1].lower() in (".gizmo", ".py", ".nk")])
        for _, _, files in os.walk(_GIZMO_DIR)
    )
    print("[My Gizmos] {} item(s) loaded from {}".format(total, _GIZMO_DIR))


def build_tools_menu():
    menubar = nuke.menu("Nuke")
    tm      = menubar.addMenu("My Tools", icon="my_menu_icon.png")
    _build_menu(tm, _TOOLS_DIR, _TOOLS_DIR, _add_py_cmd)
    _append_utility_items(tm)

    total = sum(
        len([f for f in files if f.lower().endswith(".py") and not f.startswith((".", "_"))])
        for _, _, files in os.walk(_TOOLS_DIR)
    )
    print("[My Tools]  {} script(s) loaded from {}".format(total, _TOOLS_DIR))


build_gizmos_menu()
build_tools_menu()

# -- Register drag-and-drop callback ------------------------------------------
nukescripts.addDropDataCallback(_drop_data_handler)
print("[Plugin Manager] Drag & drop install enabled - drop .gizmo / .py onto the DAG.")