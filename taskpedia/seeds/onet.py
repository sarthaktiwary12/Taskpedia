"""
O*NET Database Loader.

Loads the complete O*NET database which contains:
- 1,016 occupations
- 18,796 task statements
- 2,087 Detailed Work Activities (DWAs)
- 332 Intermediate Work Activities (IWAs)
- 41 Generalized Work Activities (GWAs)

The O*NET hierarchy is:
    Major Occupation Group (23) → Occupation (1016) → Task (18796)

Work Activities hierarchy:
    GWA (41) → IWA (332) → DWA (2087) → Tasks (18796)

This is the most comprehensive source of WORK-related tasks.
Data source: O*NET 30.1 (https://www.onetcenter.org/database.html)

The database is automatically downloaded on first use.
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from urllib.request import urlretrieve

# O*NET database download URL
ONET_VERSION = "30_1"
ONET_DOWNLOAD_URL = f"https://www.onetcenter.org/dl_files/database/db_{ONET_VERSION}_excel.zip"
ONET_TEXT_URL = f"https://www.onetcenter.org/dl_files/database/db_{ONET_VERSION}_text.zip"

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "taskpedia" / "onet"


@dataclass
class Occupation:
    """An O*NET occupation."""

    code: str  # O*NET-SOC Code (e.g., "11-1011.00")
    title: str  # e.g., "Chief Executives"
    description: str  # Full description
    major_group: str  # First 2 digits (e.g., "11")

    @property
    def major_group_name(self) -> str:
        """Get the major group name."""
        return SOC_MAJOR_GROUPS.get(self.major_group, "Unknown")


@dataclass
class TaskStatement:
    """An O*NET task statement."""

    task_id: str
    occupation_code: str
    task: str  # The actual task description
    task_type: str  # "Core" or "Supplemental"


@dataclass
class DetailedWorkActivity:
    """A Detailed Work Activity (DWA)."""

    dwa_id: str
    iwa_id: str
    title: str


@dataclass
class IntermediateWorkActivity:
    """An Intermediate Work Activity (IWA)."""

    iwa_id: str
    gwa_id: str  # Parent GWA element ID
    title: str


# SOC Major Occupation Groups (23 categories)
SOC_MAJOR_GROUPS = {
    "11": "Management",
    "13": "Business and Financial Operations",
    "15": "Computer and Mathematical",
    "17": "Architecture and Engineering",
    "19": "Life, Physical, and Social Science",
    "21": "Community and Social Service",
    "23": "Legal",
    "25": "Educational Instruction and Library",
    "27": "Arts, Design, Entertainment, Sports, and Media",
    "29": "Healthcare Practitioners and Technical",
    "31": "Healthcare Support",
    "33": "Protective Service",
    "35": "Food Preparation and Serving Related",
    "37": "Building and Grounds Cleaning and Maintenance",
    "39": "Personal Care and Service",
    "41": "Sales and Related",
    "43": "Office and Administrative Support",
    "45": "Farming, Fishing, and Forestry",
    "47": "Construction and Extraction",
    "49": "Installation, Maintenance, and Repair",
    "51": "Production",
    "53": "Transportation and Material Moving",
    "55": "Military Specific",
}


def download_onet(cache_dir: Path | None = None, force: bool = False) -> Path:
    """
    Download O*NET database if not already cached.

    Args:
        cache_dir: Directory to cache the data. Defaults to ~/.cache/taskpedia/onet
        force: Force re-download even if cached

    Returns:
        Path to the extracted data directory
    """
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    marker_file = cache_dir / ".downloaded"
    if marker_file.exists() and not force:
        return cache_dir

    print(f"Downloading O*NET database ({ONET_VERSION})...")
    print(f"  Source: {ONET_TEXT_URL}")
    print(f"  Cache:  {cache_dir}")

    # Download zip file
    zip_path = cache_dir / "onet.zip"

    def _progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            print(f"\r  Progress: {percent}%", end="", flush=True)

    urlretrieve(ONET_TEXT_URL, zip_path, _progress)
    print()  # newline after progress

    # Extract
    print("  Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        # O*NET zips have a subdirectory, extract files directly to cache_dir
        for member in zf.namelist():
            # Get just the filename, skip directories
            filename = Path(member).name
            if filename and filename.endswith(".txt"):
                # Read and write to flatten structure
                with zf.open(member) as src:
                    (cache_dir / filename).write_bytes(src.read())

    # Clean up zip
    zip_path.unlink()

    # Create marker
    marker_file.write_text(f"version={ONET_VERSION}\n")

    print("  Done!")
    return cache_dir


class ONetDatabase:
    """
    Loader for the O*NET database files.

    Usage:
        db = ONetDatabase()  # Auto-downloads if needed
        db.load()

        # Get all occupations
        for occ in db.occupations.values():
            print(f"{occ.code}: {occ.title}")

        # Get tasks for an occupation
        tasks = db.get_tasks_for_occupation("11-1011.00")
    """

    def __init__(self, data_dir: str | Path | None = None):
        """
        Initialize the O*NET database loader.

        Args:
            data_dir: Path to O*NET data. If None, downloads automatically.
        """
        if data_dir is None:
            # Auto-download
            self.data_dir = download_onet()
        else:
            self.data_dir = Path(data_dir)
            if not self.data_dir.exists():
                raise FileNotFoundError(f"O*NET data not found at {self.data_dir}")

        self.occupations: dict[str, Occupation] = {}
        self.tasks: list[TaskStatement] = []
        self.dwas: dict[str, DetailedWorkActivity] = {}
        self.iwas: dict[str, IntermediateWorkActivity] = {}

        self._tasks_by_occupation: dict[str, list[TaskStatement]] = {}
        self._dwas_by_iwa: dict[str, list[DetailedWorkActivity]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all O*NET data files."""
        if self._loaded:
            return

        self._load_occupations()
        self._load_tasks()
        self._load_iwas()
        self._load_dwas()

        self._loaded = True

    def _load_occupations(self) -> None:
        """Load occupation data."""
        path = self.data_dir / "Occupation Data.txt"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                code = row.get("O*NET-SOC Code", "")
                if not code:
                    continue

                major_group = code.split("-")[0] if "-" in code else code[:2]

                self.occupations[code] = Occupation(
                    code=code,
                    title=row.get("Title", "").strip(),
                    description=row.get("Description", "").strip(),
                    major_group=major_group,
                )

    def _load_tasks(self) -> None:
        """Load task statements."""
        path = self.data_dir / "Task Statements.txt"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                task = TaskStatement(
                    task_id=row.get("Task ID", ""),
                    occupation_code=row.get("O*NET-SOC Code", ""),
                    task=row.get("Task", "").strip(),
                    task_type=row.get("Task Type", "Core"),
                )
                self.tasks.append(task)

                # Index by occupation
                occ_code = task.occupation_code
                if occ_code not in self._tasks_by_occupation:
                    self._tasks_by_occupation[occ_code] = []
                self._tasks_by_occupation[occ_code].append(task)

    def _load_iwas(self) -> None:
        """Load Intermediate Work Activities."""
        path = self.data_dir / "IWA Reference.txt"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                iwa_id = row.get("IWA ID", "")
                if not iwa_id:
                    continue

                self.iwas[iwa_id] = IntermediateWorkActivity(
                    iwa_id=iwa_id,
                    gwa_id=row.get("Element ID", ""),
                    title=row.get("IWA Title", "").strip(),
                )

    def _load_dwas(self) -> None:
        """Load Detailed Work Activities."""
        path = self.data_dir / "DWA Reference.txt"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                dwa_id = row.get("DWA ID", "")
                iwa_id = row.get("IWA ID", "")
                if not dwa_id:
                    continue

                dwa = DetailedWorkActivity(
                    dwa_id=dwa_id,
                    iwa_id=iwa_id,
                    title=row.get("DWA Title", "").strip(),
                )
                self.dwas[dwa_id] = dwa

                # Index by IWA
                if iwa_id not in self._dwas_by_iwa:
                    self._dwas_by_iwa[iwa_id] = []
                self._dwas_by_iwa[iwa_id].append(dwa)

    def get_tasks_for_occupation(self, occ_code: str) -> list[TaskStatement]:
        """Get all tasks for an occupation."""
        return self._tasks_by_occupation.get(occ_code, [])

    def get_dwas_for_iwa(self, iwa_id: str) -> list[DetailedWorkActivity]:
        """Get all DWAs for an IWA."""
        return self._dwas_by_iwa.get(iwa_id, [])

    def get_occupations_by_major_group(self, major_group: str) -> list[Occupation]:
        """Get all occupations in a major group."""
        return [o for o in self.occupations.values() if o.major_group == major_group]

    def get_major_groups(self) -> dict[str, str]:
        """Get all major occupation groups."""
        return SOC_MAJOR_GROUPS.copy()

    def iter_all_tasks(self) -> Iterator[TaskStatement]:
        """Iterate over all task statements."""
        yield from self.tasks

    def iter_occupations(self) -> Iterator[Occupation]:
        """Iterate over all occupations."""
        yield from self.occupations.values()

    def get_stats(self) -> dict[str, int]:
        """Get database statistics."""
        return {
            "occupations": len(self.occupations),
            "tasks": len(self.tasks),
            "dwas": len(self.dwas),
            "iwas": len(self.iwas),
            "major_groups": len(SOC_MAJOR_GROUPS),
        }

    def print_hierarchy(self, max_per_group: int = 3) -> None:
        """Print the occupation hierarchy."""
        for major_code, major_name in sorted(SOC_MAJOR_GROUPS.items()):
            occs = self.get_occupations_by_major_group(major_code)
            print(f"\n[{major_code}] {major_name} ({len(occs)} occupations)")

            for occ in occs[:max_per_group]:
                tasks = self.get_tasks_for_occupation(occ.code)
                print(f"  {occ.title} ({len(tasks)} tasks)")
                for task in tasks[:2]:
                    print(f"    - {task.task[:70]}...")


def load_onet(data_dir: str | Path | None = None) -> ONetDatabase:
    """
    Load the O*NET database (downloads automatically if needed).

    Args:
        data_dir: Path to the O*NET data directory. If None, auto-downloads.

    Returns:
        Loaded ONetDatabase instance.
    """
    db = ONetDatabase(data_dir)
    db.load()
    return db
