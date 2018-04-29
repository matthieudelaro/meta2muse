import subprocess
import sys
import os


def checkRequirements():
    requirementsPath = os.path.join(
        os.path.split(os.path.abspath(sys.modules[__name__].__file__))[0],
        'requirements.txt'
    )
    print('Looking at requirements in {}'.format(requirementsPath))
    # upgrade package installer
    subprocess.check_call(
        ["python", '-m', 'pip', 'install', "--upgrade", 'pip==10.*'])
    # upgrade requirements
    with open(requirementsPath, 'rt') as requirementsFile:
        requirements = requirementsFile.readlines()
    requirements = [r.strip() for r in requirements]
    subprocess.check_call(
        ["python", '-m', 'pip', 'install', '--upgrade'] + requirements)


if __name__ == '__main__':
    checkRequirements()
    # TODO: upgrade the code from GitHub, with specific branch (one for each purpose)
