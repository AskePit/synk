import subprocess
import wmi
from dataclasses import dataclass

def get_disc_id_by_letter(letter: str) -> tuple[str, str]:
    drive_letter = letter.upper() + ':'
    c = wmi.WMI()

    for logical_disk in c.Win32_LogicalDisk():
        if logical_disk.DeviceID == drive_letter:
            for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
                for drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                    model = drive.Model.strip() if drive.Model else 'Unknown'
                    serial = drive.SerialNumber.strip() if drive.SerialNumber else 'Unknown'
                    return [model, serial]
    return ['', '']

def get_wmic_value(query, key):
    try:
        output = subprocess.check_output(["wmic", query, "get", key], text=True)
        lines = [line.strip() for line in output.splitlines() if line.strip() and key not in line]
        return lines[0] if lines else None
    except Exception:
        return None

@dataclass
class PC:
    name: str
    bios_serial: str
    board_serial: str
    system_uuid: str
    cpu_id: str
    drive_letters: list[str]

    @staticmethod
    def make_this_pc() -> 'PC':
        bios_serial = get_wmic_value("bios", "SerialNumber")
        board_serial = get_wmic_value("baseboard", "SerialNumber")
        system_uuid = get_wmic_value("csproduct", "UUID")
        cpu_id = get_wmic_value("cpu", "ProcessorId")
        return PC(name='', bios_serial=bios_serial, board_serial=board_serial, system_uuid=system_uuid, cpu_id=cpu_id, drive_letters=[])

    def equals(self, other: 'PC') -> bool:
        return (self.bios_serial == other.bios_serial and
                self.board_serial == other.board_serial and
                self.system_uuid == other.system_uuid and
                self.cpu_id == other.cpu_id)

    def serialize(self) -> str:
        return f'[PC.{self.name}]\nbios_serial = {self.bios_serial}\nboard_serial = {self.board_serial}\nsystem_uuid = {self.system_uuid}\ncpu_id = {self.cpu_id}\nletters = {" ".join(self.drive_letters)}'

@dataclass
class ExternalDisc:
    name: str
    model: str
    serial: str

    @staticmethod
    def make_from_letter(letter: str) -> 'ExternalDisc':
        model, serial = get_disc_id_by_letter(letter)
        return ExternalDisc(name='', model=model, serial=serial)
    
    def get_letter(self) -> str:
        c = wmi.WMI()

        for logical_disk in c.Win32_LogicalDisk():
            for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
                for drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                    m = drive.Model.strip() if drive.Model else 'Unknown'
                    s = drive.SerialNumber.strip() if drive.SerialNumber else 'Unknown'
                    if m == self.model and s == self.serial:
                        return logical_disk.DeviceID.replace(':', '')
        
        return ''

    def equals(self, other: 'ExternalDisc') -> bool:
        return self.model == other.model and self.serial == other.serial

    def serialize(self) -> str:
        return f'[EXT.{self.name}]\nmodel = {self.model}\nserial = {self.serial}'
