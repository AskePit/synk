import configparser
import glob
from dataclasses import dataclass, field
from pathlib import Path
from common import PC, ExternalDisc
import pprint

DEBUG = True
def dprint(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

@dataclass
class AnalyzeLog:
    @dataclass
    class FileMetadata:
        path: Path
        size: int
        mtime: float

    @dataclass
    class NoFileMessage:
        hasPaths: list[Path]
        noPaths: list[Path]

    @dataclass
    class FilesDifferMessage:
        files: list['FileMetadata'] = field(default_factory=list)

    files_diff_log : list[FilesDifferMessage] = field(default_factory=list)
    structure_diff_log : list[NoFileMessage] = field(default_factory=list)

    def add_no_file_message(self, hasPaths: list[Path], noPaths: list[Path]):
        filtered_no_paths = []
        existing_no_paths = set()
        for msg in self.structure_diff_log:
            if isinstance(msg, self.NoFileMessage):
                existing_no_paths.update(msg.noPaths)

        for np in noPaths:
            if not any(np == ep or np.is_relative_to(ep) for ep in existing_no_paths):
                filtered_no_paths.append(np)
        noPaths = filtered_no_paths
        if not noPaths:
            return

        self.structure_diff_log.append(self.NoFileMessage(hasPaths=hasPaths, noPaths=noPaths))

    def add_files_differ_message(self, files: list[FileMetadata]):
        self.files_diff_log.append(self.FilesDifferMessage(files=files))

@dataclass
class ConfigData:
    dirs: list[Path] = field(default_factory=list)
    devices: list[PC | ExternalDisc] = field(default_factory=list)

@dataclass
class Data:
    dirs: dict[str, list[Path]] = field(default_factory=dict)
    devices: list[PC | ExternalDisc] = field(default_factory=list)

    def analyze_all_dirs(self) -> AnalyzeLog:
        log = AnalyzeLog()
        for root in self.dirs.keys():
            self._analyze_root_dir(root, log)
        return log

    def _analyze_root_dir(self, root: Path, log: AnalyzeLog) -> AnalyzeLog:
        if root not in self.dirs:
            return None

        dir_versions = self.dirs[root]

        if len(dir_versions) < 2:
            return None

        visited: set[Path] = set()
        self._analyze_dir_recursively(dir_versions, visited, log, root)

    def _analyze_dir_recursively(self, dir_versions: list[Path], visited: set[Path], log: AnalyzeLog, root: Path):
        dprint(f"Recursively analyzing directories: {dir_versions}")

        for lead_dir in dir_versions:
            if not lead_dir.exists() or not lead_dir.is_dir():
                continue

            dprint(f"Go hard: {lead_dir}")

            root_path = Path(f'{lead_dir.drive}\\') / root

            for f_str in glob.glob(f'{lead_dir}/*', recursive=False):
                f = Path(f_str)
                root_relpath = f.relative_to(root_path)
                relpath = f.relative_to(lead_dir)

                if root_relpath in visited:
                    continue
                visited.add(root_relpath)

                sub_versions = [dv / relpath for dv in dir_versions]

                # Analyze this file or directory
                if f.is_dir():
                    dprint(f"Analyzing directory: {f}")
                    self._analyze_dir(sub_versions, log)
                elif f.is_file():
                    dprint(f"Analyzing file: {f}")
                    self._analyze_file(sub_versions, log)

                # If it's a directory, recurse into it
                if f.is_dir():
                    self._analyze_dir_recursively(sub_versions, visited, log, root)

    def _analyze_dir(self, dir_versions: list[Path], log: AnalyzeLog):
        for f in dir_versions:
            if not f.exists():
                hasPaths = [fv for fv in dir_versions if fv.exists()]
                noPaths = [fv for fv in dir_versions if not fv.exists()]
                log.add_no_file_message(hasPaths=hasPaths, noPaths=noPaths)

    def _analyze_file(self, file_versions: list[Path], log: AnalyzeLog):
        for f in file_versions:
            if not f.exists():
                hasPaths = [fv for fv in file_versions if fv.exists()]
                noPaths = [fv for fv in file_versions if not fv.exists()]
                log.add_no_file_message(hasPaths=hasPaths, noPaths=noPaths)

        for lead_i, lead_file in enumerate(file_versions):
            if not lead_file.exists():
                continue
            for compare_file in file_versions[lead_i + 1:]:
                if not compare_file.exists():
                    continue

                size_1 = lead_file.stat().st_size
                size_2 = compare_file.stat().st_size
                mtime_1 = lead_file.stat().st_mtime
                mtime_2 = compare_file.stat().st_mtime

                if size_1 != size_2 or mtime_1 != mtime_2:
                    log.add_files_differ_message(files=[
                        AnalyzeLog.FileMetadata(path=lead_file, size=size_1, mtime=mtime_1),
                        AnalyzeLog.FileMetadata(path=compare_file, size=size_2, mtime=mtime_2),
                    ])
    
def load_config() -> ConfigData:
    data = ConfigData()

    config = configparser.ConfigParser()
    config.read('config.ini')
    for section in config.sections():
        if section.startswith('PC.'):
            '''
            [PC.pc_name]
            bios_serial = xxx
            board_serial = xxx
            system_uuid = xxx
            cpu_id = xxx
            letters = C D
            '''
            name = section[3:]
            bios_serial = config[section].get('bios_serial', '')
            board_serial = config[section].get('board_serial', '')
            system_uuid = config[section].get('system_uuid', '')
            cpu_id = config[section].get('cpu_id', '')
            drive_letters = [l.strip().upper() for l in config[section].get('letters', '').split(' ') if l.strip()]
            pc = PC(name=name, bios_serial=bios_serial, board_serial=board_serial, system_uuid=system_uuid, cpu_id=cpu_id, drive_letters=drive_letters)
            data.devices.append(pc)
        elif section.startswith('EXT.'):
            '''
            [EXT.name]
            model = xxx
            serial = xxxxxxxxx
            '''
            name = section[4:]
            model = config[section].get('model', '')
            serial = config[section].get('serial', '')
            disc = ExternalDisc(name=name, model=model, serial=serial)
            data.devices.append(disc)
        elif section == 'dirs':
            '''
            [dirs]
            paths = 
                folder1
                folder3/subfolder2/subsubfolder
                folder2/subfolder
            '''
            paths = config[section].get('paths', '')
            for path_str in paths.split('\n'):
                path_str = path_str.strip()
                if not path_str:
                    continue
                path = Path(path_str)
                data.dirs.append(path)
    return data

def find_this_pc(devices: list[PC | ExternalDisc]) -> PC | None:
    this_pc = PC.make_this_pc()
    for item in devices:
        if isinstance(item, PC) and item.equals(this_pc):
            return item
    return None

def find_all_external_discs(devices: list[PC | ExternalDisc]) -> list[ExternalDisc]:
    found_discs = []
    for item in devices:
        if isinstance(item, ExternalDisc):
            letter = item.get_letter()
            if letter:
                found_discs.append(item)
    return found_discs

def find_dirs_for_letter(letter: str, dirs: list[Path]) -> dict[str, list[Path]]:
    existing_dirs = {}
    for base_dir in dirs:
        full_path = Path(f'{letter}:\\') / base_dir
        if full_path.exists() and full_path.is_dir():
            if base_dir not in existing_dirs:
                existing_dirs[base_dir] = []
            existing_dirs[base_dir].append(full_path)
    return existing_dirs

def update_dict(target: dict[str, list[Path]], source: dict[str, list[Path]]):
    for key, value in source.items():
        if key not in target:
            target[key] = []
        target[key].extend(value)

def find_all_dirs(devices: list[PC | ExternalDisc], dirs: list[Path]) -> dict[str, list[Path]]:
    existing_dirs = {}
    for dev in devices:
        if isinstance(dev, PC):
            for letter in dev.drive_letters:
                update_dict(existing_dirs, find_dirs_for_letter(letter, dirs))
        elif isinstance(dev, ExternalDisc):
            letter = dev.get_letter()
            if letter:
                update_dict(existing_dirs, find_dirs_for_letter(letter, dirs))
    return existing_dirs

def main():
    configData = load_config()
    availableData = Data()

    pc = find_this_pc(configData.devices)
    if pc:
        #print(f'Registered PC found: {pc.serialize()}')
        availableData.devices.append(pc)
    else:
        print('This PC is not registered.')
        exit(1)

    discs = find_all_external_discs(configData.devices)
    for disc in discs:
        #print(disc.serialize())
        availableData.devices.append(disc)

    availableData.dirs = find_all_dirs(availableData.devices, configData.dirs)
    #print(availableData)

    analised = availableData.analyze_all_dirs()
    pprint.pprint(analised)

if __name__ == "__main__":
    main()