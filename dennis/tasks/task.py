import re
import os
import git
import time
import github
import logging

from .utils import version_key, DennisException
from .repo import DirectoryRepoProvider

_log = logging.getLogger(__name__)


VERSION_REGEX = 'v([0-9]+\.)+'
RELEASE_PR_PATTERN = re.compile('Release {}'.format(VERSION_REGEX))
RELEASE_BRANCH_PATTERN = re.compile(
    '(origin/)?testrelease/{}'.format(VERSION_REGEX)
)
REPO_PATTERN = re.compile('([^/:]+/[^/\.]+)(.git)?$')


def wait_while_false(cmd, wait_for_minutes, *args):
    start_time = time.time()

    def minutes_passed():
        return int((time.time() - start_time) / 60)

    is_true = cmd(*args)
    while not is_true and minutes_passed() < wait_for_minutes:
        _log.info('Sleeping for 10 seconds and checking again...')
        time.sleep(10)
        is_true = cmd(*args)

    return is_true


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

        _log.info('Searching for ongoing releases in {}...'.format(
            self.repo_name
        ))
        self.meta['release_branch'] = self._get_open_release_branch()

        if self.meta['release_branch']:
            _log.info('Found release branch. Searching for open PR...')
            self.meta['release_pr'] = self._get_open_release_pr()
            self.meta['release_branch_name'] = self.meta[
                'release_branch'
            ].ref.remote_head
            self.meta['release_tag_name'] = self.meta[
                'release_branch'
            ].name.split('/')[-1]
            _log.info('Searching for existing GitHub release...')
            self.meta['release'] = self._get_release_for_tag(
                self.meta['release_tag_name']
            )
        else:
            self.meta['release_pr'] = None
            self.meta['release_branch'] = None
            self.meta['release_branch_name'] = None

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

    def _format_release_pr_name(self, version):
        return 'Release {}'.format(version)

    def _get_open_release_branch(self):
        branches = self.repo.remotes.origin.fetch()

        release_branches = [
            b
            for b in branches
            if re.match(RELEASE_BRANCH_PATTERN, b.name)
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

    def _get_open_release_pr(self):
        issues = list(self.github_repo.get_issues())

        open_prs = [
            issue.pull_request
            for issue in issues
            if re.match(RELEASE_PR_PATTERN, issue.title)
        ]

        if not any(open_prs):
            _log.warn(
                'No open pull requests found in repo {}'.format(
                    self.repo_name
                )
            )
            return None

        release_pr_data = open_prs[0].raw_data
        release_pr_number = int(release_pr_data['url'].split('/')[-1])

        return self.github_repo.get_pull(
            release_pr_number
        )

    def _get_release_for_tag(self, tag):
        try:
            return self.github_repo.get_release(tag)
        except:
            return None

    def _checkout_and_pull(self, name):
        _log.info('Checking out and pulling {}'.format(name))
        branch = self.repo.heads.__getattr__(name)
        try:
            branch.checkout()
        except git.exc.GitCommandError:
            raise DennisException(
                'Failed to checkout {}, most likely '
                'because you have some local changes.'
                ' Please stash your changes.'.format(
                    name)
            )

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

    def _merge(self, pull_request, wait_for_minutes=0):
        if not self.draft:
            passed = self._have_checks_passed(pull_request)
            if (
                not passed and
                wait_for_minutes > 0
            ):
                _log.info(
                    'Going into while loop until checks have passed'
                    ' or until {} minutes have gone by'.format(
                        wait_for_minutes
                    )
                )
                passed = wait_while_false(
                    self._have_checks_passed,
                    wait_for_minutes,
                    pull_request
                )

            if passed:
                pull_request.merge()
            else:
                raise DennisException(
                    'Build checks for PR "{}" didn\'t'
                    'pass, not merging'.format(
                        pull_request.title
                    )
                )

    def _merge_branches(self, base, head, message):
        if not self.draft:
            self.github_repo.merge(
                base, head, message
            )

    def _have_checks_passed(self, pull_request):
        last_commit = list(
            pull_request.get_commits()
        )[-1]
        return all([
            status.state == 'passed'
            for status in last_commit.get_statuses()
        ])
