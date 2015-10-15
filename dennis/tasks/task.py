import re
import os
import git
import github
import logging

from .utils import version_key
from .repo import DirectoryRepoProvider

_log = logging.getLogger(__name__)


VERSION_PATTERN = re.compile('v([0-9]+\.)+')
REPO_PATTERN = re.compile('([^/:]+/[^/\.]+)(.git)?$')


class Task:

    changelog_name = 'CHANGELOG.md'
    changelog_path = None

    pr_id_name = '.release_pr_id'
    pr_id_path = None

    repo_provider = None

    repo = None

    github_repo = None

    repo_owner = None

    repo_name = None

    draft = False

    meta = {}

    def __init__(
        self, github_user=None,
        github_token=None, project_dir=None,
        draft=False, **kwargs
    ):
        self.repo_provider = DirectoryRepoProvider(project_dir)
        self.repo = self.repo_provider.get()

        self.github_user = github_user
        self.github_token = github_token
        self.draft = draft

        repo_url = self.repo.remotes.origin. \
            config_reader.config.get('remote "origin"', 'url')

        self.repo_name = re.search(REPO_PATTERN, repo_url).groups()[0]

        self.github_repo = github.Github(
            self.github_user, github_token
        ).get_repo(self.repo_name)

        import pdb
        pdb.set_trace()

        self.repo_owner = self.github_repo.owner.login

        # Checkout latest changes for this repo
        self._checkout_and_pull('develop')

        self.pr_id_path = os.path.join(
            self.repo.working_dir, self.pr_id_name
        )

        self.meta['last_tag'] = self._get_latest_tag()

        if not self.meta['last_tag']:
            self.meta['last_tag_name'] = None
        else:
            self.meta['last_tag_name'] = self.meta['last_tag'].name

        self.meta['release_branch'] = self._get_current_release()

        if self.meta['release_branch']:
            self.meta['release_branch_name'] = self.meta[
                'release_branch'
            ].ref.remote_head
            self.meta['release_tag_name'] = self.meta[
                'release_branch'
            ].name.split('/')[-1]
        else:
            self.meta['release_branch'] = None
            self.meta['release_branch_name'] = None
            self.meta['pr_id'] = None

        self.changelog_path = os.path.join(
            self.repo.working_dir, self.changelog_name
        )

    def run(self):
        """Release process task."""
        raise NotImplementedError

    def _get_latest_tag(self):
        tags = self.repo.tags.copy()

        tags.sort(
            key=lambda tag: (
                    version_key(tag.name.strip('v'))
                )
        )

        if not any(tags):
            return None

        return tags[-1]

    def _format_release_branch_name(self, version):
        return 'testrelease/{}'.format(version)

    def _get_current_release(self):
        branches = self.repo.remotes.origin.fetch()

        release_branches = [
            b
            for b in branches
            if re.match(VERSION_PATTERN, b.name.split('/')[-1])
        ]

        if not any(release_branches):
            return None

        release_branches.sort(
            key=lambda b: (
                    version_key(
                        b.name.split('/')[-1].strip('v')
                    )
                )
        )

        last_version = release_branches[-1].name.split('/')[-1].strip('v')
        latest_tag_version = self.meta['last_tag'].name.strip('v')

        if version_key(latest_tag_version) < version_key(last_version):
            return release_branches[-1]

        return None

    def _checkout_and_pull(self, name):
        _log.info('Checking out and pulling {}'.format(name))
        branch = self.repo.heads.__getattr__(name)
        branch.checkout()
        self.repo.remotes.origin.pull(
            refspec='{0}:{0}'.format(self.repo.active_branch.name)
        )

    def _commit_all(self, message):
        _log.info('Committing all changes: {}'.format(
            message
        ))
        #
        # Using the Git object as a last resort, couldn't
        # find the equivalent inside the library
        #
        git.Git(self.repo.working_dir).execute(
            ['git', 'commit', '-a', '-m', '"(dennis) {}"'.format(message)]
        )

    def _push(self):
        _log.info('Pushing branch {} upstream'.format(
            self.repo.active_branch.name
        ))
        self.repo.remotes.origin.push(
            refspec='{0}:{0}'.format(self.repo.active_branch.name)
        )

    def _merge(self, pull_request):
        if not self.draft:
            pull_request.merge()

    def _add_pr_id(self, pr_id):
        with open(self.pr_id_path, 'w') as pr_id_file:
            pr_id_file.write(str(pr_id))
        self.repo.index.add([self.pr_id_path])

    def _get_pr_id(self):
        with open(self.pr_id_path, 'r') as pr_id_file:
            return int(pr_id_file.read().strip())
