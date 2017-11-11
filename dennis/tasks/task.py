import re
import os
import git
import time
import github
import logging

from .utils import (
    DennisException,
    VERSION_REGEX,
    format_release_branch_name,
    format_release_pr_name
)

_log = logging.getLogger(__name__)

RELEASE_PR_PATTERN = re.compile('Release {}'.format(VERSION_REGEX))
RELEASE_BRANCH_PATTERN = re.compile(
    '(origin/)?release/{}'.format(VERSION_REGEX)
)

# kalohq/dennis.git
REPO_PATTERN = re.compile('([^/:]+/[^/\.]+)(.git)?$')


def wait_while_result_satisfies(
    cmd, does_result_satisfy, wait_for_minutes, *args
):
    start_time = time.time()

    def minutes_passed():
        return int((time.time() - start_time) / 60)

    while (
        does_result_satisfy(cmd(*args)) and
        minutes_passed() < wait_for_minutes
    ):
        _log.info('Sleeping for 10 seconds and checking again...')
        time.sleep(10)


class Release:
    # Release branch name
    name = None

    # (Release Artifact) Release branch
    branch = None

    # (Release Artifact) Release PR object
    pr = None

    def __init__(self, version_type):
        self.name = format_release_branch_name(version_type)
        self.version_type = version_type

    def is_started(self):
        return self.branch is not None


class Task:
    repo_provider = None

    # Git object
    repo = None

    # GitHub object
    github_repo = None

    # Repository owner name
    repo_owner = None

    # Repository name
    repo_name = None

    # Whether this is a draft run
    draft = False

    # Last release SHA
    last_version = None

    # Current release artifacts
    release = None

    # Type of release
    version_type = None

    def __init__(
        self,
        github_user=None,
        pickup=None,
        github_token=None,
        project_dir=os.getcwd(),
        version_type=None,
        draft=False,
        **kwargs
    ):
        self.repo = git.Repo(project_dir)
        self.github_user = github_user
        self.github_token = github_token
        self.draft = draft
        self.version_type = version_type

        repo_url = self.repo.remotes.origin. \
            config_reader.config.get('remote "origin"', 'url')
        self.repo_name = re.search(REPO_PATTERN, repo_url).groups()[0]

        self.github_repo = github.Github(
            self.github_user, github_token
        ).get_repo(self.repo_name)

        self.repo_owner = self.github_repo.owner.login
        self.repo_name = self.github_repo.name

        # Check out latest released state
        _log.info('Checking out and pulling master')
        self._checkout_and_pull('master')
        last_release_sha = self.repo.heads.master.commit.hexsha

        # Check out latest changes for this repo
        _log.info('Checking out and pulling develop')
        self._checkout_and_pull('develop')

        self.last_version = last_release_sha
        _log.info('Last release SHA in {}: {}'.format(
            self.repo_name, self.last_version
        ))

        self.release = self._get_release_artifacts(version_type)

    def run(self):
        """Release process task."""
        raise NotImplementedError

    def _get_release_artifacts(self, version_type):
        release = Release(version_type)

        _log.info(
            'Gathering release artifacts'
            ' in project {} for {} release:'.format(
                self.repo_name, version_type)
        )

        _log.info('\t- release branch...')
        release.branch = self._get_branch(release.name)
        if not release.branch:
            return None

        _log.info('\t- release PR...')
        release.pr = self._get_open_pr(
            format_release_pr_name(version_type)
        )

        return release

    def _get_branch(self, name):
        try:
            return self.repo.remotes.origin.fetch(refspec=name)
        except git.exc.GitCommandError:
            return None

    def _get_open_pr(self, name):
        issues = list(self.github_repo.get_issues())

        open_prs = [
            issue.pull_request
            for issue in issues
            if name == issue.title
        ]

        if not any(open_prs):
            _log.warn(
                'No open pull requests found in repo {}'.format(
                    self.repo_name
                )
            )
            return None

        pr = open_prs[0]

        pr_data = pr.raw_data
        pr_number = int(pr_data['url'].split('/')[-1])

        return self.github_repo.get_pull(pr_number)

    def _checkout(self, name):
        try:
            self.repo.git.checkout(name)
        except git.exc.GitCommandError:
            raise DennisException(
                'Failed to checkout {}, most likely '
                'because you have some local changes.'
                ' Please stash your changes.'.format(
                    name)
            )

    def _checkout_and_pull(self, name):
        self._checkout(name)
        self.repo.remotes.origin.pull(
            refspec='{0}:{0}'.format(self.repo.active_branch.name)
        )

    def _commit_all(self, message):
        _log.info('Committing changes: {}'.format(
            message
        ))
        try:
            # Using the Git object as a last resort, couldn't
            # find the equivalent inside the library
            git.Git(self.repo.working_dir).execute(
                ['git', 'commit', '-a', '-m', '"(dennis) {}"'.format(message)]
            )
        except git.exc.GitCommandError:
            _log.info('No changes to commit')

    def _branch_contains_commit(self, branch, commit):
        output = git.Git(self.repo.working_dir).execute(
            ['git', 'branch', '--contains', commit]
        )
        branches = output.split('\n')

        if not any(branches):
            return False

        branches = [b.strip(' *\n\r') for b in branches]

        return branch in branches

    def _push(self):
        _log.info('Pushing branch {} upstream'.format(
            self.repo.active_branch.name
        ))
        self.repo.remotes.origin.push(
            refspec='{0}:{0}'.format(self.repo.active_branch.name)
        )

    def _merge(self, pull_request, wait_for_minutes=0):
        passed = self._have_checks_passed(pull_request)
        if (
            passed == 'pending' and
            wait_for_minutes > 0
        ):
            _log.info(
                'Going into while loop until checks have passed'
                ' or until {} minutes have gone by'.format(
                    wait_for_minutes
                )
            )
            wait_while_result_satisfies(
                self._have_checks_passed,
                lambda result: result.lower() == 'pending',
                wait_for_minutes,
                pull_request
            )
            passed = self._have_checks_passed(pull_request)

        if not self.draft:
            if passed in ['passed', 'success']:
                pull_request.merge()
                return True
            else:
                _log.error(
                    'Build checks for PR {} did not pass'
                    ', cannot merge',
                    pull_request.title
                )
                raise DennisException(
                    'Build checks for PR "{}" didn\'t'
                    ' pass, not merging'.format(
                        pull_request.title
                    )
                )

        return False

    def _merge_branches(self, base, head, message):
        if not self.draft:
            _log.info(
                'Merging {} into {} remotely'.format(
                    head, base
                )
            )
            self.github_repo.merge(
                base, head, message
            )
            _log.info(
                'Successfully merged'.format(
                    head, base
                )
            )

    def _have_checks_passed(self, pull_request):
        last_commit = list(
            pull_request.get_commits()
        )[-1]

        if not any(last_commit.get_statuses()):
            return 'passed'

        statuses = list(last_commit.get_statuses())
        statuses.sort(
            key=lambda status: status.created_at
        )

        _log.info(
            'There are {} statuses. Using only most recent one: {}'.format(
                len(statuses),
                {
                    'source': statuses[-1].target_url,
                    'state': statuses[-1].state
                }
            )
        )

        return statuses[-1].state
