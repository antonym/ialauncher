import os
import shutil
import subprocess
from zipfile import ZipFile
from urllib import request
from urllib.parse import quote, unquote
from configparser import RawConfigParser

from .dosbox import get_dosbox_path

DOSBOX = get_dosbox_path()

class Game:
    def __init__(self, path):
        self.path = path
        self.gamedir = os.path.join(self.path, 'dosbox_drive_c')
        self.identifier = os.path.basename(path)
        self.config = c = RawConfigParser()
        c.read(os.path.join(path, 'metadata.ini'))
        self.title = c['metadata'].get('title')
        self.year = c['metadata'].get('year')
        self.emulator_start = c['metadata'].get('emulator_start')
        self.dosbox_conf = c['metadata'].get('dosbox_conf')
        self.url = c['metadata'].get('url')
        if self.url:
            self.url = self.url.split()

    def __gt__(self, other):
        return self.identifier > other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def start(self, autorun=True):
        """
        Start the game in one of two modes:

        1. autorun=True

            Paste the contents of `emulator_start` into dosbox.bat, and
            run it. Dosbox will exit when the game ends.

        2. autorun=False

            Do as above, but don't run dosbox.bat and don't exit Dosbox.
            Any changes made to dosbox.bat will be save as the
            `emulator_start` variable in metadata.ini.

        The frontend allows starting the game in the second mode by pressing
        Alt-Enter. This allows the user to do the following from within dosbox:

            C:\> echo MYGAME.BAT >> dosbox.bat
            C:\> exit

        These changes will then be preserved for the next time the game
        is run normally. Make sure to commit any useful additions!

        """
        if not os.path.isdir(self.gamedir):
            self.download_files()
        os.chdir(self.gamedir)
        batfile = os.path.join(self.gamedir, 'dosbox.bat')
        conffile = os.path.join(self.gamedir, 'dosbox.conf')
        dosbox_args = ['-fullscreen']
        dosbox_run = '.'

        if self.dosbox_conf:
            with open(conffile, 'w') as f:
                f.write(self.dosbox_conf)
            dosbox_args.extend(['-userconf', '-conf', 'dosbox.conf'])

        if self.emulator_start:
            if autorun:
                if os.path.isfile(self.emulator_start):

                    # Special case for many games that currently only
                    # contain the name of the executable
                    dosbox_run = self.emulator_start

                else:
                    dosbox_run = 'dosbox.bat'
                    with open(batfile, 'w') as f:
                        f.write('@echo off\ncls\n')
                        f.write(self.emulator_start)

            else:
                with open(batfile, 'w') as f:
                    f.write(self.emulator_start)

        else:
            autorun = False
            if not os.path.isfile(batfile):
                with open(batfile, 'w') as f:
                    f.write('\n')

        if autorun:
            dosbox_args.append('-exit')
        else:
            dosbox_run = '.'

        child_process = subprocess.Popen([DOSBOX, dosbox_run] + dosbox_args)

        if not autorun:
            child_process.wait()
            if os.path.isfile(batfile):
                with open(batfile, 'r') as f:
                    self.emulator_start = f.read()
                    if self.emulator_start:
                        self.write_metadata()

    def download_files(self, autorun=True):
        os.chdir(self.path)
        for u in self.url:
            filename = unquote(u.split('/')[-1])
            if not os.path.isfile(filename):
                print('Downloading', filename)
                request.urlretrieve(u, filename)
            if filename.endswith('zip') or filename.endswith('ZIP') or filename.endswith('play'):
                print('Extracting', filename)
                self.extract_file(filename)
            else:
                os.makedirs(self.gamedir, exist_ok=True)
                shutil.copy(filename, self.gamedir)

    def extract_file(self, zipfile):
        with ZipFile(zipfile, 'r') as f:
            f.extractall(self.gamedir)
        if os.path.isfile(os.path.join(self.gamedir, 'dosbox.conf')):
            os.remove(os.path.join(self.gamedir, 'dosbox.conf'))

    def write_metadata(self):
        if self.title:
            self.config['metadata']['title'] = self.title
        if self.year:
            self.config['metadata']['year'] = self.year
        if self.url:
            self.config['metadata']['url'] = '\n'.join(self.url)
        if self.emulator_start:
            self.config['metadata']['emulator_start'] = self.emulator_start
        if self.dosbox_conf:
            self.config['metadata']['dosbox_conf'] = self.dosbox_conf
        inifile = os.path.join(self.path, 'metadata.ini')
        with open(inifile, 'w') as f:
            self.config.write(f)

    def get_titlescreen(self):
        path = os.path.join(self.path, 'title.png')
        if os.path.isfile(path):
            return path
        else:
            return None

    def urlencoded(self):
        return quote(self.identifier)
