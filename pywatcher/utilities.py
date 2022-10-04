from unidecode import unidecode
from os.path import basename
from pathlib import Path
from PyPDF2 import PdfReader
from watchdog.utils.patterns import filter_paths
from watchdog.utils.dirsnapshot import DirectorySnapshot, DirectorySnapshotDiff
from watchdog.events import FileCreatedEvent
from .config import settings
import time, re, pickle
import pdfplumber

class RenameFile:
    YEAR_NOT_FOUND = "00"
    MONTH_NOT_FOUND = "00"
    TYPE_NOT_FOUND = "AAA"

    def __init__(self, path):
        self.path = unidecode(path).lower()
        self.name= self.__convert()
        self.year = "20" + self.__get_year()
        self.month = self.__get_month()
        self.type = self.__get_type()
        self.basename = self.__get_name()

    def __convert(self):
        return f"{self.__get_month()}{self.__get_year()} - {self.__get_type()} - {self.__get_name()}"

    def __get_name(self):
        return basename(self.path)

    def __get_type(self) -> str:
        for i, (type, code) in enumerate(settings.types.items()):
            if unidecode(self.path.lower()).find(type) != -1:
                return code
        return self.TYPE_NOT_FOUND

    def __match_months(self, item):
        return next((code for i, (month, code) in enumerate(settings.months.items()) if item.find(month) != -1), None)

    def __get_infos(self):
        values = [{"value" : x, "match" : self.__match_months(x)} for x in self.path.split('\\') if self.__match_months(x) is not None]
        return values[0] if len(values) > 0 else None
    
    def __get_year(self):
        return self.__get_infos()["value"][-2:] if self.__get_infos() is not None else self.YEAR_NOT_FOUND

    def __get_month(self):
        return self.__get_infos()["match"] if self.__get_infos() is not None else self.MONTH_NOT_FOUND


class Backups():
    def __init__(self, path: str) -> None:
        self.path = path
        self.backups = self.get_backups()

    def get_backups(self) -> list[Path]:
        backups = []
        for file in Path(self.path).iterdir():
            if file.is_file():
                backups.append(file)
        return backups

    def get_latest(self) -> Path | None:
        latest = None
        for file in self.backups:
            if latest is None:
                latest = file
            elif file.stat().st_mtime > latest.stat().st_mtime:
                latest = file
        return latest

    def get_oldest(self) -> Path | None:
        oldest = None
        for file in self.backups:
            if oldest is None:
                oldest = file
            elif file.stat().st_mtime < oldest.stat().st_mtime:
                oldest = file
        return oldest

    def remove_latest(self) -> None:
        latest = self.get_latest()
        if latest is not None:
            latest.unlink()

    def remove_oldest(self) -> None:
        oldest = self.get_oldest()
        if oldest is not None:
            oldest.unlink()

    def process(self):
        if len(self.backups) > settings.default.max_backups:
            self.remove_oldest()


class PDFParser():
    ERROR_MSG = "Error parsing PDF"
    def __init__(self, filepath: str) -> None:
        self.file = filepath

    def get_text(self):
        blankRegex = r"[\s\u0000-\u001F\uFFF0-\uFFF8\u007F\u115F\u1160\u3164\uFFA0\uFFFC]+"
        text = ''
        try:
            with pdfplumber.open(self.file) as pdf:
                for page in pdf.pages:
                    replaced = re.sub(blankRegex, " ", page.extract_text())
                    text += replaced
            return text
        except:
            return self.ERROR_MSG


class Snapshot():
    PICKLE_DIR = Path(__file__).parent.joinpath('cache')
    FIRST_RUN_MSG = "No new files found"

    def __init__(self, path: str) -> None:
        self.path = path

    def shot(self):
        snapshot = DirectorySnapshot(self.path)
        with open(Path(self.PICKLE_DIR).joinpath(f"snapshot_{time.time_ns()}.pickle"), 'wb') as f:
            pickle.dump(snapshot, f)
        Backups(self.PICKLE_DIR).process()
        return snapshot

    def diff(self) -> DirectorySnapshotDiff | None:
        snapshot = Backups(self.PICKLE_DIR).get_latest()
        if snapshot is not None:
            snapshot = pickle.load(open(snapshot, 'rb'))
            diffSnapshot = DirectorySnapshotDiff(
                snapshot, DirectorySnapshot(self.path))
            return diffSnapshot
        return None

    def resume(self):
        diffSnapshot = self.diff()
        if diffSnapshot is None:
            return self.FIRST_RUN_MSG

        return [FileCreatedEvent(file) for file in filter_paths(
            diffSnapshot.files_created, 
            settings.default.patterns, 
            settings.default.ignore_patterns, 
            settings.default.case_sensitive
            )] if settings.default.ignore_directories else [FileCreatedEvent(file) for file in diffSnapshot.files_created]

class ContentParser():
    def __init__(self, filepath: str) -> None:
        self.renamed_file = RenameFile(filepath)
        self.content = PDFParser(filepath).get_text()

    def get_content(self):
        return self.content
    
    def get_partner(self):
        try:
            return self.renamed_file.name.replace(".pdf", "").split(' - ')[3].upper()
        except:
            return None

    def get_client(self): 
        try:
            return self.renamed_file.name.replace(".pdf", "").split(' - ')[2].upper()
        except:
            return None

    def get_date(self):
        return f"{self.renamed_file.month}/{self.renamed_file.year}"

    def get_year(self):
        return self.renamed_file.year

    def get_month(self):
        return self.renamed_file.month

    def get_basename(self):
        return self.renamed_file.basename

    def get_filename(self):
        return self.renamed_file.name

    def get_type(self):
        return "Sous-Traitant" if self.renamed_file.type == "SST" else "Fournisseur" if self.renamed_file.type == "FRS" else "Autre"

    def get_devis(self):
        regex = r"de[0-9]{7}"
        return re.search(regex, self.get_basename()).group(0).upper() if re.search(regex, self.get_basename()) is not None else None

    def get_sum(self):
        r1 = r"Total HT (.*?) €"
        r2 = r"Total HT (.*?) Total TVA"
        r3 = r"TOTAL H.T: (.*?) €"

        match_cases = [r1, r2, r3]
        for case in match_cases:
            if re.search(case, self.content):
                matched = re.search(case, self.content).group(1)
                if len(matched) < 10:
                    return matched.replace(',', '.')
        return None