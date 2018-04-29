import subprocess


def checkRequirements():
    # upgrade package installer
    subprocess.check_call(
        ["python3", '-m', 'pip', 'install', "--upgrade", 'pip==10.*'])
    # upgrade requirements
    with open('requirements.txt', 'rt') as requirementsFile:
        requirements = requirementsFile.readlines()
    requirements = [r.strip() for r in requirements]
    subprocess.check_call(
        ["python3", '-m', 'pip', 'install', '--upgrade'] + requirements)


if __name__ == '__main__':
    checkRequirements()
    # TODO: upgrade the code from GitHub, with specific branch (one for each purpose)
