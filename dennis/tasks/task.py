import re
import os
import git
import time
import github
import logging

from .utils import (
    version_key, DennisException,
    VERSION_REGEX, get_next_version_options,
    format_release_branch_name, format_release_pr_name
)

_log = logging.getLogger(__name__)

RELEASE_PR_PATTERN = re.compile('Release {}'.format(VERSION_REGEX))
RELEASE_BRANCH_PATTERN = re.compile(
    '(origin/)?release/{}'.format(VERSION_REGEX)
)
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

    # Release version
    version = None

    # Release branch name
    name = None

    # (Release Artifact) Release branch
    branch = None

    # (Release Artifact) Release PR object
    pr = None

    # (Release Artifact) GitHub release object
    github_release = None

    # (Release Artifact) Is merged back into develop
    merged_back = False

    def __init__(self, version):
        self.version = version
        self.name = format_release_branch_name(version)

    def is_started(self):
        return self.branch is not None

    def is_complete(self):
        return (
            all([
                self.branch,
                self.merged_back,
                self.github_release])
        )


class Task:

    changelog_name = 'CHANGELOG.md'
    changelog_path = None

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

    # Current release version
    version = None

    # Last release version
    last_version = None

    # Current release artifacts
    release = None

    # Last release artifacts
    # last_release = None

    def __init__(
        self, github_user=None, pickup=None,
        github_token=None, project_dir=os.getcwd(),
        version=None, version_type=None,
        draft=False, **kwargs
    ):
        self.repo = git.Repo(project_dir)

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
        self.repo_name = self.github_repo.name

        # Checkout latest changes for this repo
        _log.info('Checking out and pulling develop')
        self._checkout_and_pull('develop')

        last_tag = self._get_latest_tag()

        if not last_tag:
            raise DennisException(
                'dennis cannot yet handle projects without at least'
                ' one tag, sorry!'
            )

        _log.info('Last release version in {}: {}'.format(
            self.repo_name, last_tag.name
        ))

        self.last_version = last_tag.name
        self.version = version

        # Set version based on version type if needed
        if version is None and version_type is not None:
            self.version = get_next_version_options(
                self.last_version
            )[version_type]

        self.release = self._get_release_artifacts(self.version)

        # if not self.release:
        # self.last_release = self._get_release_artifacts(self.last_version)

        self.changelog_path = os.path.join(
            self.repo.working_dir, self.changelog_name
        )

    def run(self):
        """Release process task."""
        raise NotImplementedError

    def _get_release_artifacts(self, version):
        release = Release(version)

        _log.info(
            'Gathering release artifacts'
            ' in project {} for version {}:'.format(
                self.repo_name, release.version)
        )

        _log.info('\t- release branch...')
        release.branch = self._get_branch(release.name)

        if not release.branch:
            return None

        _log.info('\t- release PR...')
        release.pr = self._get_open_pr(
            format_release_pr_name(release.version)
        )

        _log.info('\t- is release merged back into develop...')
        last_commit = release.branch[0].commit.hexsha
        release.merged_back = self._branch_contains_commit(
            'develop', last_commit
        )

        _log.info('\t- GitHub release...')
        release.github_release = self._get_github_release(
            release.version
        )

        return release

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

    def _get_github_release(self, tag):
        try:
            return self.github_repo.get_release(tag)
        except:
            return None

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
