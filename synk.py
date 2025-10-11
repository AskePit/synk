import configparser
from dataclasses import dataclass, field
from pathlib import Path
from common import PC, ExternalDisc

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
        files: list[FileMetadata] = field(default_factory=list)

    log : list[NoFileMessage | FilesDifferMessage] = field(default_factory=list)

    # TODO: Proper methods to add and merge messages
    def add_no_file_message(self, hasPaths: list[Path], noPaths: list[Path]):
        self.log.append(self.NoFileMessage(hasPaths=hasPaths, noPaths=noPaths))

    def add_files_differ_message(self, files: list[FileMetadata]):
        self.log.append(self.FilesDifferMessage(files=files))

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
        for key in self.dirs.keys():
            dir_log = self.analyze_dir(key)
            if dir_log:
                log.log.extend(dir_log.log)
        return log

    def analyze_dir(self, key: Path) -> AnalyzeLog:
        if key not in self.dirs:
            return None

        dirs = self.dirs[key]

        if len(dirs) < 2:
            return None

        log = AnalyzeLog()
        # TODO: Perform analysis and populate log
        return log


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
        print(f'Checking {full_path}')
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
        print(f'Registered PC found: {pc.serialize()}')
        availableData.devices.append(pc)
    else:
        print('This PC is not registered.')
        exit(1)

    discs = find_all_external_discs(configData.devices)
    for disc in discs:
        print(disc.serialize())
        availableData.devices.append(disc)

    availableData.dirs = find_all_dirs(availableData.devices, configData.dirs)
    print(availableData)

if __name__ == "__main__":
    main()