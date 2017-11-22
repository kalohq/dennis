import os
import logging
import random

from .utils import (
    run_command,
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
PR_DESCRIPTION = (
    '![]({})'
    '\n\n'
    'We’re on our way to a much simpler release process. This release branch'
    ' is therefore minimal. I’m not making any changes here. It’s still fine'
    ' for you to make some last-minute tweaks, but remember – soon that chance'
    ' is going away, because release branches will no longer be a thing.'
    '\n\n'
    'Here’s my advice though. Make sure your code is ready to go by the time'
    ' you merge it to develop. Soon there will be no other way!'
    '\n\n'
    'Yours sincerely,'
    '\nDennis (Bot)'
)


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

    def __init__(
        self, branch=None, **kwargs
    ):
        super().__init__(**kwargs)

        # Validate the source branch being used for the new release branch
        # is one of the expected branches for this release type
        if not branch == 'develop':
            ALLOWED_BRANCHES['hotfix'].append(branch)
        if branch not in ALLOWED_BRANCHES[self.version_type]:
            message = (
                'With a release type "{}" you are not allowed'
                ' to branch off "{}". The branches you can use are: {}.'
                ' If you are creating a hotfix, you may use master or any'
                ' non-develop branch'.format(
                    self.release_type,
                    branch,
                    ALLOWED_BRANCHES[self.release_type]
                )
            )
            _log.error(message)
            raise DennisException(message)

        self.branch = branch

        self.release_script_path = os.path.join(
            self.repo.working_dir, self.release_script_name
        )

    def run(self):
        if self.release:
            _log.warn(
                'This release seems to be already ongoing, continuing'
                ' to cover any missed steps'
            )

        # Release branch name
        if self.release:
            release_branch_name = self.release.name
        else:
            release_branch_name = format_release_branch_name(
                self.version_type
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
            _log.info('Creating new branch for {} release'.format(
                self.version_type
            ))
            release_branch = self.repo.create_head(release_branch_name)
        else:
            release_branch = self.release.branch

        # Checkout release branch
        _log.info('Checking out release branch: {}'.format(
            release_branch_name))
        self._checkout(release_branch_name)

        # Run the release script
        if not self.release:
            if os.path.isfile(self.release_script_path):
                _log.info('Running {} script inside {}'.format(
                    self.release_script_name, self.repo_name
                ))
                output, success, return_code = run_command(
                    [
                        self.release_script_path,
                        self.last_version
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
            release_pr_description = PR_DESCRIPTION.format(random.choice([
                'https://media.giphy.com/media/3o6Ztn3DaJ41FDHVwA/giphy.gif',
                'https://media.giphy.com/media/l0HlFwETpLZyast9u/giphy.gif',
                'https://media.giphy.com/media/l0HlTP1jCtsx1Xl4s/giphy.gif',
                'https://media.giphy.com/media/l0HlIT8WBMsYENnG0/giphy.gif',
                'https://media.giphy.com/media/l0HlHnIwSCFBq2ySQ/giphy.gif',
                'https://media.giphy.com/media/3o6Zt51xm4FZJcBy7e/giphy.gif',
                'https://media.giphy.com/media/3o6ZtmFYFy93Lg1LwI/giphy.gif',
                'https://media.giphy.com/media/eK3GNqMBif63C/giphy.gif',
                'https://media.giphy.com/media/d1FKUVRyHv9Sgy64/giphy.gif',
            ]))
            release_pr = self.github_repo.create_pull(
                format_release_pr_name(self.version_type),
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
