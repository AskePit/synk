from common import get_disc_id_by_letter, get_wmic_value, PC, ExternalDisc
from typing import Callable

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

def register_pc():
    name = input('Enter PC name: ')
    letters = input('Enter drive letters you want to track (ex. c d e): ').split()
    letters = [l.upper() for l in letters]

    pc = PC.make_this_pc()
    pc.name = name
    pc.drive_letters = letters

    pc_string = pc.serialize()
    with open('config.ini', 'a') as f:
            f.write('\n\n')
            f.write(pc_string)

def register_external_disc():
    letter = input('Enter disc\'s drive letter: ').upper()
    name = input('Enter disc name: ')

    disc = ExternalDisc.make_from_letter(letter)
    disc.name = name

    disc_string = disc.serialize()
    with open('config.ini', 'a') as f:
        f.write('\n\n')
        f.write(disc_string)

def main():
    menu_choice('You want to register a PC or external disc?', [
        ('PC', register_pc),
        ('External disc', register_external_disc),
    ])

if __name__ == "__main__":
    main()