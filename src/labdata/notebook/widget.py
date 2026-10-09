import heapq
import os
import re
from pathlib import Path

import ipywidgets as widgets
import pyperclip
from IPython.display import HTML, display

from labdata import config
from labdata.notebook.view import viewer


class ViewWidget:
    def __init__(self, path=None, limit=5):
        self.path = config.DATA_FOLDER if path is None else path
        self.limit = limit
        self.files = {}

        self.init_gui()
        self.init_sig()
        self.init_val()

    def init_gui(self):
        self.lstDir = widgets.SelectMultiple(
            layout=widgets.Layout(width="800px", height="92px"),
        )
        self.btnView = widgets.Button(
            description="View",
            layout=widgets.Layout(width="100px", height="44px"),
        )
        self.btnFile = widgets.ToggleButton(
            description="Files",
            layout=widgets.Layout(width="100px", height="44px"),
        )
        self.txtFile = widgets.HTML(layout=widgets.Layout(width="900px"))

        buttons = widgets.VBox([self.btnView, self.btnFile])
        stylesheet = Path(config.WIDGET_CSS).read_text(encoding="utf-8")
        self.box = widgets.VBox([
            widgets.HBox([buttons, self.lstDir]),
            self.txtFile,
        ])
        self.box.add_class("labdata-view-widget")
        display(self.box)
        display(HTML(f'<style type="text/css">{stylesheet}</style>'))

    def init_sig(self):
        self.btnView.on_click(self.on_btnView_clicked)
        self.btnFile.observe(self.on_btnFile_changed, "value")
        self.lstDir.observe(self.on_lstDir_changed, "value")

    def init_val(self):
        self.files = self.recent(self.path, self.limit)
        directories = list(self.files)

        if directories:
            root = Path(self.path)
            self.lstDir.options = [
                (os.path.relpath(directory, root), directory)
                for directory in directories
            ]
            self.lstDir.value = (directories[0],)
        else:
            self.lstDir.disabled = True
            self.btnView.disabled = True
            self.btnFile.disabled = True

    @staticmethod
    def modified(stat):
        created = getattr(stat, "st_birthtime", stat.st_mtime)
        return max(stat.st_mtime, created)

    @classmethod
    def recent(cls, path, limit):
        pattern = re.compile(config.DATA_FILE_PATTERN)
        queue = []
        path = os.fsdecode(path)
        heapq.heappush(queue, (-cls.modified(os.stat(path)), path))
        found = {}

        while queue and len(found) < limit:
            _, directory = heapq.heappop(queue)
            files = []
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        modified = cls.modified(entry.stat(follow_symlinks=False))
                        heapq.heappush(queue, (-modified, entry.path))
                    elif (
                        entry.is_file(follow_symlinks=False)
                        and pattern.fullmatch(entry.name)
                    ):
                        files.append(entry.path)
            if files:
                found[directory] = sorted(files)

        return found

    def selected_files(self):
        return [
            filename
            for directory in self.lstDir.value
            for filename in self.files[directory]
        ]

    def on_btnView_clicked(self, button):
        viewer(self.selected_files())

    def on_btnFile_changed(self, change):
        if change["new"]:
            self.txtFile.value = "<p>" + "<p>".join(
                f'<a href="{filename}">{filename}</a>'
                for filename in self.selected_files()
            )
        else:
            self.txtFile.value = ""

    def on_lstDir_changed(self, change):
        self.btnFile.value = False
        pyperclip.copy("\n".join(
            f'R"{directory}",'
            for directory in self.lstDir.value
        ))
