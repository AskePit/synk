import configparser
import wmi

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    for section in config.sections():
        print(f'[{section}]')
        for key, value in config[section].items():
            print(f'{key} = {value}')
        print()

if __name__ == "__main__":
    main()