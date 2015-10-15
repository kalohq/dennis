import sys
import argparse
import tasks
import logging
import getpass

_log = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(
        format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO
    )
    logging.getLogger('requests').setLevel('WARN')
    logging.getLogger('PyGithub').setLevel('WARN')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'action',
        choices=['prepare', 'release', 'changelog']
    )

    parser.add_argument(
        '--type',
        default=None,
        choices=tasks.RELEASE_TYPES,
        help='Release type. Indicates which of'
        ' vX.Y.Z to increment (major = X, minor = Y, fix = Z).'
        ' Ignore if --version is provided.'
    )

    parser.add_argument(
        '--version',
        default=None,
        choices=tasks.RELEASE_TYPES,
        help='Release version. Overrides --type.'
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
        help='Don\'t do any merges and only create draft release'
    )

    args = parser.parse_args()

    if not args.github_user:
        _log.error('GitHub username argument --user must be provided')
        sys.exit(1)

    if args.action == 'prepare' and not (args.type or args.version):
        _log.error(
            'One of release type --type or'
            ' release version --version must be provided'
        )
        sys.exit(1)

    github_token = args.github_token or getpass.getpass()

    action = args.action

    configure_logging()

    task = tasks.TASKS[action](
        new_version=args.version,
        new_version_type=args.type,
        project_dir=args.project_dir,
        github_user=args.github_user,
        github_token=github_token,
        draft=args.draft
    )

    task.run()

main()
