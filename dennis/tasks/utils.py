import subprocess

VERSION_REGEX = 'v([0-9]+\.)+'


def format_release_branch_name(version):
    return 'release/{}'.format(version)


def format_release_pr_name(version):
    return 'Release {}'.format(version)


def version_key(version):
    return list(map(int, (version).split('.')))


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


def get_next_version_options(version):
    version = version or 'v0.0.0'
    version = version.strip('v')

    UPGRADES = {
        'major': 0,
        'minor': 1,
        'hotfix': 2
    }

    def recompile(key):
        return 'v' + ('.'.join(map(str, key)))

    def upgrade(key, type):
        key[UPGRADES[type]] += 1
        for lower_key in range(UPGRADES[type] + 1, len(key)):
            key[lower_key] = 0
        return key

    key = version_key(version)

    return {
        k: recompile(upgrade(key.copy(), k))
        for k, v in UPGRADES.items()
    }
