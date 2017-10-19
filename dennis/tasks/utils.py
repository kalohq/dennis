import subprocess

VERSION_REGEX = 'v([0-9]+\.)+'


def format_release_branch_name(version_type):
    return 'release/current-{}'.format(version_type)


def format_release_pr_name(version_type):
    return 'Ongoing release ({})'.format(version_type)


def run_command(args, cwd=None):
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    output = proc.communicate()
    if proc.returncode == 0:
        return output[0], True, proc.returncode
    else:
        return output[1], False, proc.returncode


class DennisException(Exception):
    """
        Generic exception
    """
