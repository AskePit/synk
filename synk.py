import configparser
from pathlib import Path
from common import PC, ExternalDisc

dirs: list[Path] = []
registered: list[PC | ExternalDisc] = []
available: list[PC | ExternalDisc] = []

def load_config():
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
            registered.append(pc)
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
            registered.append(disc)
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
                dirs.append(path)

def find_this_pc() -> PC | None:
    this_pc = PC.make_this_pc()
    for item in registered:
        if isinstance(item, PC) and item.equals(this_pc):
            return item
    return None

def find_all_external_discs() -> list[ExternalDisc]:
    found_discs = []
    for item in registered:
        if isinstance(item, ExternalDisc):
            letter = item.get_letter()
            if letter:
                found_discs.append(item)
    return found_discs

def main():
    load_config()
    pc = find_this_pc()
    if pc:
        print(f'Registered PC found: {pc.serialize()}')
        available.append(pc)
    else:
        print('This PC is not registered.')

    discs = find_all_external_discs()
    if discs:
        print('Registered external discs found:')
        for disc in discs:
            print(disc.serialize())
            available.append(disc)
    else:
        print('No registered external discs found.')
    
    print(dirs)

if __name__ == "__main__":
    main()