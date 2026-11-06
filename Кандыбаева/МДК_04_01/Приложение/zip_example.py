"""Пример использования zipfile для ПР 3.4."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

with TemporaryDirectory() as directory:
    path = Path(directory) / "example.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("readme.txt", "Учебный пример")
    with ZipFile(path) as archive:
        print("Файлы в архиве:", ", ".join(archive.namelist()))
        print("Содержимое:", archive.read("readme.txt").decode("utf-8"))
