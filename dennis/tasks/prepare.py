import os
import logging

from .utils import (
    run_command,
    get_next_version_options,
    DennisException,
    format_release_branch_name,
    format_release_pr_name
)
from .task import Task

_log = logging.getLogger(__name__)

RELEASE_TYPES = ['major', 'minor', 'hotfix']
ALLOWED_BRANCHES = {
    'major': ['develop'],
    'minor': ['develop'],
    'hotfix': ['master']
}


class PrepareTask(Task):
    """
        Steps taken:

        - Create new branch with new tag
        - Execute the release script release.sh
        - Commit changes and Push
        - Create PR into master

    """

    release_script_path = None
    release_script_name = 'release'
    has_release_script = None

    def __init__(
        self, branch=None, release_md=True, **kwargs
    ):
        super().__init__(**kwargs)

        # Validate branch value against planned version value
        next_version_options = get_next_version_options(self.last_version)
        release_type = [
            release_type
            for release_type, release_version in next_version_options.items()
            if release_version == self.version
        ]

        # Validate the version upgrading to is one of the
        # expected next versions
        if not any(release_type):
            message = (
                'The version you are trying to upgrade to ({})'
                ' is not one of the expected next versions: {}'.format(
                    self.version, list(next_version_options.values())
                )
            )
            _log.error(message)
            raise DennisException(message)

        release_type = release_type[0]

        # Validate the source branch being used for the new release branch
        # is one of the expected branches for this release type
        if not branch == 'develop':
            ALLOWED_BRANCHES['hotfix'].append(branch)
        if branch not in ALLOWED_BRANCHES[release_type]:
            message = (
                'With a release type "{}" ({} -> {}) you are not allowed'
                ' to branch off "{}". The branches you can use are: {}.'
                ' If you are creating a hotfix, you may use master or any'
                ' non-develop branch'.format(
                    release_type, self.last_version, self.version,
                    branch, ALLOWED_BRANCHES[release_type]
                )
            )
            _log.error(message)
            raise DennisException(message)

        self.branch = branch
        self.release_md = release_md

        self.release_script_path = os.path.join(
            self.repo.working_dir, self.release_script_name
        )
        self.has_release_script = os.path.isfile(self.release_script_path)

    def run(self):
        if self.release:
            _log.warn(
                'This release seems to be already ongoing, continuing'
                ' to cover any missed steps'
            )

        # Get new version
        new_version = self.version

        # Release branch name
        if self.release:
            release_branch_name = self.release.name
        else:
            release_branch_name = format_release_branch_name(
                new_version
            )

        # If local branch exists
        if (
            not self.release and
            self._does_local_branch_exist(release_branch_name)
        ):
            _log.warn(
                'Found local branch with the same'
                ' name {}, deleting that stuff'.format(
                    release_branch_name
                )
            )
            self.repo.delete_head(release_branch_name, '-D')

        # Checkout the source branch
        _log.info('Checking out and pulling source branch: {}'.format(
            self.branch))
        self._checkout_and_pull(self.branch)

        # Create release branch
        if not (self.release and self.release.branch):
            _log.info('Creating new release branch with version {}'.format(
                new_version
            ))
            release_branch = self.repo.create_head(release_branch_name)
        else:
            release_branch = self.release.branch

        # Checkout release branch
        _log.info('Checking out release branch: {}'.format(
            release_branch_name))
        self._checkout(release_branch_name)

        # Bump the version etc.
        if not self.release:
            if self.has_release_script:
                _log.info('Running {} script inside {}'.format(
                    self.release_script_name, self.repo_name
                ))
                output, success, return_code = run_command(
                    [
                        self.release_script_path,
                        self.last_version,
                        new_version
                    ],
                    cwd=self.repo.working_dir
                )
                if not success:
                    raise DennisException(
                        'Failed to run release script {} with code {}'
                        ' and output {}'.format(
                            self.release_script_path, return_code, output
                        )
                    )
            else:
                _log.warn(
                    'No release script ({}) was found'
                    ' in the project root'.format(
                        self.release_script_name))

        if not self.release:
            # Commit changes
            self._commit_all('Initial Release Commit')

            # Push upstream
            _log.info('Pushing new release branch upstream')
            self._push()

            # Setting upstream for convenience
            self.repo.remotes.origin.fetch()
            refs = [
                r
                for r in self.repo.remotes.origin.refs
                if r.name == 'origin/{}'.format(release_branch_name)
            ]
            if any(refs):
                release_branch.set_tracking_branch(
                    refs[0]
                )

        # Create pull request
        if not (self.release and self.release.pr):
            release_pr_description = ''

            if self.release_md:
                with open('RELEASE.md', 'r') as release_md:
                    release_pr_description = release_md.read()

            release_pr = self.github_repo.create_pull(
                format_release_pr_name(new_version),
                release_pr_description, 'master',
                self.repo.active_branch.name
            )
        else:
            release_pr = self.release.pr

        # Done
        _log.info(
            'All done. You may now proceed to the required QA testing'
            ' and, when happy, come back to dennis and hit "dennis release"'
            '\n\n'
            'Find the PR @ {}'.format(
                release_pr.html_url
            )
        )

    def _does_local_branch_exist(self, name):
        return len([head for head in self.repo.heads if head.name == name]) > 0
