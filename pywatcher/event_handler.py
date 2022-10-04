from watchdog.events import PatternMatchingEventHandler
from .utilities import ContentParser, Snapshot
from .google import GDrive, GSheets
from .config import settings

class PatternEventHandler(PatternMatchingEventHandler):
    def __init__(self):
        super().__init__(
            settings.default.patterns, 
            settings.default.ignore_patterns, 
            settings.default.ignore_directories, 
            settings.default.case_sensitive)

    def on_any_event(self, event):
        super().on_any_event(event)
        Snapshot(settings.default.path).shot()

    def on_moved(self, event):
        super().on_moved(event)

    def on_created(self, event):
        super().on_created(event)
        parsed = ContentParser(event.src_path)
        renamed = parsed.get_filename()
        text = parsed.get_content()
        client = parsed.get_client()
        partner = parsed.get_partner()
        date = parsed.get_date()
        somme = parsed.get_sum()
        type = parsed.get_type()
        devis = parsed.get_devis()
        basename = parsed.get_basename()
        url = GDrive().upload(event.src_path, renamed)

        GSheets().insert([["", "", partner, client, type, devis, date, url, renamed, basename, text, somme]])

    def on_deleted(self, event):
        super().on_deleted(event)

    def on_modified(self, event):
        super().on_modified(event)