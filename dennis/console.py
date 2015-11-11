import re
import sys
import argparse
import logging
import getpass

import coloredlogs

from . import tasks

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
        choices=tasks.RELEASE_TYPES,
        help='Release type. Indicates which of'
        ' vX.Y.Z to increment (major = X, minor = Y, hotfix = Z).'
        ' \'hotfix\' will branch off master.'
        ' Option is ignored if --version is provided.'
    )

    parser.add_argument(
        '--version',
        default=None,
        help='Release version in the format vX.Y.Z. Overrides --type.'
        ' Will branch off master by default, use --branch to override.'
    )

    parser.add_argument(
        '--branch',
        default=None,
        help='Branch from which to create a new release.'
        ' Used only when --version is specified. Default is master.'
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
        '--dir',
        dest='project_dir',
        default=None,
        help='Project directory'
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

    if not args.type and not args.version:
        _log.error(
            'One of release type --type or'
            ' release version --version must be provided'
        )
        sys.exit(1)

    if args.version:
        args.type = None

    if args.version and not args.branch:
        _log.warn(
            'You specified --version, the default is to use the'
            ' \'master\' branch for the new release branch. Use '
            '--branch if you wish to override this.'
        )

    github_token = args.github_token or getpass.getpass()

    action = args.action

    # Either --version is specified
    if args.version:

        if not re.match(
            re.compile(tasks.VERSION_REGEX), args.version
        ):
            _log.error(
                'Provided version {} does not '
                'conform with format "vX.Y.Z"'.format(
                    args.version
                )
            )
            sys.exit(1)
        args.branch = args.branch or 'master'

    # Or --version-type is specified
    elif args.type:
        if args.type == 'hotfix':
            args.branch = 'master'
        else:
            args.branch = 'develop'

    task = tasks.TASKS[action](
        version=args.version,
        version_type=args.type,
        branch=args.branch,
        project_dir=args.project_dir,
        github_user=args.github_user,
        github_token=github_token,
        draft=args.draft,
        wait_for_minutes=args.build_timeout
    )

    task.run()
