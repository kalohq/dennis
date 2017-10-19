import re
import sys
import argparse
import logging
import getpass

import coloredlogs

from .tasks import (
    TASKS, RELEASE_TYPES, VERSION_REGEX
)

_log = logging.getLogger(__name__)


def configure_logging(draft):
    coloredlogs.install(
        fmt='[%(asctime)s]{} %(message)s'.format(
                '[DRAFT]' if draft else ''
        ),
        level='INFO'
    )
    logging.getLogger('requests').setLevel('WARN')
    logging.getLogger('PyGithub').setLevel('WARN')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'action',
        choices=['prepare', 'release']
    )

    parser.add_argument(
        '--type',
        default=None,
        choices=RELEASE_TYPES,
        help='Release type. Indicates which of'
        ' vX.Y.Z to increment (major = X, minor = Y, hotfix = Z).'
        ' \'hotfix\' will branch off master.'
    )

    parser.add_argument(
        '--branch',
        default=None,
        help='Branch from which to create a new release'
    )

    parser.add_argument(
        '--user',
        dest='github_user',
        default=None,
        help='GitHub username'
    )

    parser.add_argument(
        '--token',
        dest='github_token',
        default=None,
        help='GitHub token or password'
    )

    parser.add_argument(
        '--draft',
        dest='draft',
        action='store_true',
        default=False,
        help='Don\'t do any merges, just create PRs'
    )

    parser.add_argument(
        '--build-timeout',
        dest='build_timeout',
        default=10,
        help='How many minutes to wait for the '
        'build to pass when trying to merge PR'
    )

    args = parser.parse_args()

    configure_logging(args.draft)

    if not args.github_user:
        _log.error('GitHub username argument --user must be provided')
        sys.exit(1)

    if not args.type:
        _log.error('--type must be provided')
        sys.exit(1)

    github_token = args.github_token or getpass.getpass()

    action = args.action

    if not args.branch:
        if args.type == 'hotfix':
            args.branch = 'master'
        else:
            args.branch = 'develop'

    task = TASKS[action](
        version_type=args.type,
        branch=args.branch,
        github_user=args.github_user,
        github_token=github_token,
        draft=args.draft,
        wait_for_minutes=args.build_timeout,
    )

    task.run()
