from dataclasses import dataclass
from typing import Callable
import wmi

# supports only 1-9 options!
def menu_choice(question: str, options: list[tuple[str, Callable[[], None]]]) -> None:
    print(question)
    for i, (option_text, _) in enumerate(options):
        print(f'{i + 1}. {option_text}')

    while True:
        choice = input()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            index = int(choice) - 1
            action = options[index][1]
            action()
            return
        else:
            print('Invalid choice. Please select a valid option.')

def get_disc_id_by_letter(letter: str) -> str:
    drive_letter = letter.upper() + ':'
    c = wmi.WMI()

    for logical_disk in c.Win32_LogicalDisk():
        if logical_disk.DeviceID == drive_letter:
            for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
                for drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                    model = drive.Model.strip() if drive.Model else 'Unknown'
                    serial = drive.SerialNumber.strip() if drive.SerialNumber else 'Unknown'
                    return f'{model}_{serial}'
    return ''

def get_letter_by_disc_id(disc_id: str) -> str:
    c = wmi.WMI()

    model, serial = disc_id.split('_')

    for logical_disk in c.Win32_LogicalDisk():
        for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
            for drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                m = drive.Model.strip() if drive.Model else 'Unknown'
                s = drive.SerialNumber.strip() if drive.SerialNumber else 'Unknown'
                if m == model and s == serial:
                    return logical_disk.DeviceID.replace(':', '')
    
    return ''

def get_pc_motherboard_serial():
    c = wmi.WMI()
    for motherboard in c.Win32_BaseBoard():
        return motherboard.SerialNumber.strip() if motherboard.SerialNumber else 'Unknown'
    return 'Unknown'

@dataclass
class PC:
    name: str
    motherboard_serial: str
    drive_letters: list[str]

    def flush_to_config(self):
        with open('config.ini', 'a') as f:
            f.write('\n')
            f.write(
f'''[PC.{self.motherboard_serial}]
name = {self.name}
letters = {" ".join(self.drive_letters)}'''
            )

@dataclass
class ExternalDisc:
    name: str
    disc_id: str

    def flush_to_config(self):
        with open('config.ini', 'a') as f:
            f.write('\n')
            f.write(
f'''[EXT.{self.disc_id}]
name = {self.name}'''
            )

def register_pc():
    name = input('Enter PC name: ')
    letters = input('Enter drive letters you want to track (ex. c d e): ').split()
    letters = [l.upper() for l in letters]

    motherboard_serial = get_pc_motherboard_serial()

    pc = PC(name=name, motherboard_serial=motherboard_serial, drive_letters=letters)
    pc.flush_to_config()


def register_external_disc():
    letter = input('Enter disc\'s drive letter: ').upper()
    name = input('Enter disc name: ')
    id = get_disc_id_by_letter(letter)

    disc = ExternalDisc(name=name, disc_id=id)
    disc.flush_to_config()

def main():
    menu_choice('You want to register a PC or external disc?', [
        ('PC', register_pc),
        ('External disc', register_external_disc),
    ])

if __name__ == "__main__":
    main()