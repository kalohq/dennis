import os
import logging

from .utils import version_key, text_input, run_command
from .task import Task

_log = logging.getLogger(__name__)

RELEASE_TYPES = ['major', 'minor', 'fix']


class PrepareTask(Task):
    """
        Steps taken:

        - Check out develop
        - Pull
        - Prompt for new tag version or use provided one
        - Create new branch with new tag
        - Execute the release script release.sh
        - Commit changes and Push
        - Create PR into master

    """

    release_script_path = None
    release_script_name = 'release.sh'
    has_release_script = None

    def __init__(
        self, new_version=None,
        new_version_type=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.new_version = new_version
        self.new_version_type = new_version_type

        self.release_script_path = os.path.join(
            self.repo.working_dir, self.release_script_name
        )
        self.has_release_script = os.path.isfile(self.release_script_path)

    def run(self):
        commit_required = False

        _log.info('The last tag in this repo is {}'.format(
            self.meta['last_tag']
        ))

        # If remote branch exists
        if self.meta.get('release_branch'):
            _log.info('A release branch seems to be ongoing already {}'.format(
                self.meta['release_branch'].name
            ))
            _log.info(
                '\n\nPlease checkout that branch'
                ' and continue by making code fixes to it or hit'
                ' "dennis release"'
            )
            return

        # Get latest version
        new_version = self.new_version

        # Upgrade based on given version type
        if new_version is None and self.new_version_type is not None:
            new_version = self._get_version_upgrade_choices(
                self.meta['last_tag_name']
            )[self.new_version_type]

        # Upgrade based on input version type
        if new_version is None:
            choices = self._get_version_upgrade_choices(
                self.meta['last_tag_name']
            )
            ordered_choices = RELEASE_TYPES
            new_version_type = text_input(
                'Please select the new version type as one of [{}]'
                ', which result in {} respectively'.format(
                    ', '.join(ordered_choices),
                    ', '.join([choices[c] for c in ordered_choices])
                ),
                'fix'
            )
            new_version = choices[new_version_type]

        _log.info('Creating new release branch with version {}'.format(
            new_version
        ))

        # Create new branch
        release_branch_name = self._format_release_branch_name(
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

        release_branch = self.repo.create_head(
            release_branch_name
        )
        release_branch.checkout()

        # Bump the version
        if self.has_release_script:
            _log.info('Running {} script inside {}'.format(
                self.release_script_name, self.repo_name
            ))
            output, success, return_code = run_command(
                [
                    'bash', '-x', self.release_script_path,
                    self.meta['last_tag_name'],
                    new_version
                ],
                cwd=self.repo.working_dir
            )
            if not success:
                _log.error(
                    'Failed to run release script {} with code {}'
                    ' and output {}'.format(
                        self.release_script_path, return_code, output
                    )
                )
                return
            commit_required = True
        else:
            _log.warn(
                'No release script ({}) was found in the project root'.format(
                    self.release_script_name))

        # Generate the changelog
        changelog = self._add_changelog(new_version)
        if changelog:
            commit_required = True

        # Commit changes if any
        if commit_required:
            self._commit_all('Version Bump')

        # Push upstream
        _log.info('Pushing new release branch upstream')
        self._push()

        # Create pull request
        release_pr = self.github_repo.create_pull(
            'Release {}'.format(new_version), '',
            'master', self.repo.active_branch.name
        )

        # Stick the PR ID in the branch, will remove during the release step
        self._add_pr_id(release_pr.number)
        self._commit_all('Add PR number')
        self._push()

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
            self.repo_name,
            self.meta['last_tag_name'] or 'v0.0.0',
            new_version
        ]

        _log.info(
            'Generating the changelog since the previous release.'
            ' This can take a couple minutes...'
        )
        output, success, return_code = run_command(
            sawyer_args,
            cwd=self.repo.working_dir
        )

        if not success:
            _log.error(
                'Failed to generate changelog. Ran sawyer with {}'
                ' and received error code {} with output: {}'.format(
                    ' '.join(sawyer_args),
                    return_code,
                    output
                )
            )
            return

        new_changelog = output.decode('utf-8')

        # Prepend the new changelog entries
        with open(self.changelog_path, 'r') as original:
            original_changelog = original.read()
        with open(self.changelog_path, 'w') as modified:
            modified.write(new_changelog + '\n\n' + original_changelog)

        return new_changelog

    def _does_local_branch_exist(self, name):
        return len([head for head in self.repo.heads if head.name == name]) > 0

    def _get_version_upgrade_choices(self, version):
        version = version or 'v0.0.0'
        version = version.strip('v')

        UPGRADES = {
            'major': 0,
            'minor': 1,
            'fix': 2
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
