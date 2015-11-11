import os
import re
import logging

from .utils import (
    version_key,
    run_command, VERSION_REGEX,
    DennisException,
    get_next_version_options,
    format_release_branch_name,
    format_release_pr_name
)
from .task import Task

_log = logging.getLogger(__name__)

RELEASE_TYPES = ['major', 'minor', 'hotfix']


class PrepareTask(Task):
    """
        Steps taken:

        - Create new branch with new tag
        - Execute the release script release.sh
        - Generate changelog
        - Commit changes and Push
        - Create PR into master

    """

    release_script_path = None
    release_script_name = 'release'
    has_release_script = None

    def __init__(
        self, branch=None, **kwargs
    ):
        super().__init__(**kwargs)

        self.branch = branch

        self.release_script_path = os.path.join(
            self.repo.working_dir, self.release_script_name
        )
        self.has_release_script = os.path.isfile(self.release_script_path)

    def run(self):
        _log.info('The last release version in this repo is {}'.format(
            self.last_version
        ))

        if self.release:
            _log.warn(
                'This release seems to be already ongoing, continuing'
                ' to cover any missed steps...'
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
        if self._does_local_branch_exist(release_branch_name):
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
            release_branch = self.repo.create_head(
                release_branch_name
            )

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
            # Generate the changelog
            self._add_changelog(new_version)

            # Commit changes
            self._commit_all('Initial Release Commit')

            # Push upstream
            _log.info('Pushing new release branch upstream')
            self._push()

        # Create pull request
        if not (self.release and self.release.pr):
            release_pr = self.github_repo.create_pull(
                format_release_pr_name(new_version), '',
                'master', self.repo.active_branch.name
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

    def _add_changelog(self, new_version):
        sawyer_args = [
            'sawyer', '-u',
            self.github_user, '-q',
            '-t', self.github_token,
            '{}/{}'.format(self.repo_owner, self.repo_name),
            self.last_version or 'v0.0.0',
            new_version
        ]

        _log.info(
            'Generating the changelog since the previous release.'
            ' This can take a couple of minutes...'
        )
        output, success, return_code = run_command(
            sawyer_args,
            cwd=self.repo.working_dir
        )

        if not success:
            sawyer_args[sawyer_args.index('-t')+1] = '********'
            raise DennisException(
                'Failed to generate changelog. Ran sawyer with:\n\n{}\n\n'
                'and received error code {} with output:\n\n{}'.format(
                    ' '.join(sawyer_args),
                    return_code,
                    output.decode('utf-8')
                )
            )

        new_changelog = output.decode('utf-8')

        # Prepend the new changelog entries
        with open(self.changelog_path, 'r') as original:
            original_changelog = original.read()
        with open(self.changelog_path, 'w') as modified:
            modified.write(new_changelog + '\n\n' + original_changelog)

        return new_changelog

    def _does_local_branch_exist(self, name):
        return len([head for head in self.repo.heads if head.name == name]) > 0
