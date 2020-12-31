'''
This is an alternative setup script which uses cx_Freeze to build a
Windows-native executable. Call it like this:

    C:\ialauncher>python setup_win.py bdist_msi

This will generate a working application beneath the build/ directory
and an MSI installer in the dist/ directory.

'''
import os
from cx_Freeze import setup, Executable

# Provide an executable that will run from the current directory:
with open('temp.py', 'w') as f:
    f.write('''
import multiprocessing
from ialauncher.main import main
if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
''')

setup(
    name='IA Launcher',
    version = '2.1.5',
    description = 'A DOSBox frontend for the Internet Archive',
    executables = [Executable(
        'temp.py',
        targetName='ialauncher.exe',
        base='Win32GUI',
        shortcutName='IA Launcher',
        shortcutDir='ProgramMenuFolder',
        icon='ia.ico',
    )],
)

# Remove temporary executable
os.remove('temp.py')
