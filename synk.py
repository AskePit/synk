import configparser
from dataclasses import dataclass, field
from pathlib import Path
from common import PC, ExternalDisc

@dataclass
class Data:
    dirs: list[Path] = field(default_factory=list)
    devices: list[PC | ExternalDisc] = field(default_factory=list)

def load_config() -> Data:
    data = Data()

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
            drive_letters = [l.strip().upper() for l in config[section].get('letters', '').split(',') if l.strip()]
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

def find_dirs_for_letter(letter: str, dirs: list[Path]) -> list[Path]:
    existing_dirs = []
    for base_dir in dirs:
        full_path = Path(f'{letter}:\\') / base_dir
        print(f'Checking {full_path}')
        if full_path.exists() and full_path.is_dir():
            existing_dirs.append(full_path)
    return existing_dirs

def find_all_dirs(data: Data) -> list[Path]:
    existing_dirs = []
    for dev in data.devices:
        if isinstance(dev, PC):
            for letter in dev.drive_letters:
                existing_dirs.extend(find_dirs_for_letter(letter, data.dirs))
        elif isinstance(dev, ExternalDisc):
            letter = dev.get_letter()
            if letter:
                existing_dirs.extend(find_dirs_for_letter(letter, data.dirs))
    return existing_dirs

def main():
    configData = load_config()
    data = Data()

    pc = find_this_pc(configData.devices)
    if pc:
        print(f'Registered PC found: {pc.serialize()}')
        data.devices.append(pc)
    else:
        print('This PC is not registered.')
        exit(1)

    discs = find_all_external_discs(configData.devices)
    for disc in discs:
        print(disc.serialize())
        data.devices.append(disc)
    
    data.dirs = find_all_dirs(configData)
    print(data)

if __name__ == "__main__":
    main()