import logging

from jinja2 import Template

from .task import Task
from .utils import format_release_pr_name

_log = logging.getLogger(__name__)


def jinja2_render(context, template_text):
    return Template(template_text).render(**context)


class ReleaseTask(Task):
    """
        Steps:

        - If no ongoing release, exit
        - Merge release PR into master if build passes
        - Checkout and pull release branch
        - Pull out the changelog
        - Create GitHub release using the latest changelog
        - Merge master back into develop

    """

    wait_for_minutes = 0

    def __init__(self, wait_for_minutes=0, **kwargs):
        super().__init__(**kwargs)
        self.wait_for_minutes = wait_for_minutes

    def run(self):

        if not self.release:
            _log.warn(
                'Could not find an ongoing release for {} at version {}.'
                ' Perhaps you haven\'t run "dennis prepare" yet?'
                .format(self.repo_name, self.version)
            )
            _log.warn(
                '\n\n\n'
                'Alternatively, if you intended for a previous version,'
                ' in project {}, then you can pick it up and finish the job'
                ' by re-running "dennis release" with the option'
                ' "--pickup <version>"'.format(self.repo_name)
            )
            return

        # Merge PR into master
        if self.release.pr and not self.release.pr.is_merged():
            _log.info(
                'About to merge release PR into master:'
                ' project = {}, title = {}...'.format(
                    self.repo_name, self.release.pr.title
                )
            )
            merged = self._merge(
                self.release.pr, wait_for_minutes=self.wait_for_minutes)
            if merged:
                _log.info('Release PR is merged')

        # Merge master into develop
        if not self.release.merged_back:
            self._merge_branches(
                'develop', 'master', '(dennis) Master back into Develop'
            )

        # Checkout release
        _log.info('Checking out and pulling release branch: {}'.format(
            self.release.name
        ))
        self._checkout_and_pull(self.release.name)

        # Pull out changelog
        changelog = self._get_release_changelog(
            self.last_version, self.version,
            self.repo_name, self.repo_owner
        )

        # Get latest master commit ID
        _log.info('Checking out master, to find last commit')
        self._checkout('master')
        last_commit_id = self.repo.heads.master.commit.hexsha

        # Not making releases draft-able as this introduces complication
        # when handling the real release
        github_release_url = 'N/A'
        if (
            not self.release.github_release and
            not self.draft
        ):
            # Method Signature (thanks for the docs @PyGithub)
            #
            # create_git_tag_and_release(
            #    self, tag, tag_message, release_name, release_message, object,
            #    type, tagger=github.GithubObject.NotSet,
            #    draft=False, prerelease=False
            # ):
            #
            # Publish release
            #
            _log.info('Creating GitHub release...')
            release = self.github_repo.create_git_tag_and_release(
                self.release.version,
                '', format_release_pr_name(self.release.version),
                changelog, last_commit_id, 'commit'
            )
            github_release_url = release.raw_data['html_url']
            _log.info('GitHub release created')

        # Done
        _log.info(
            '{} is merged into master, and develop has'
            ' been updated. \n\nSee the latest published release @ {}'.format(
                format_release_pr_name(self.release.version),
                github_release_url)
        )

    def _get_release_changelog(
        self, last_tag, new_tag, repo, owner
    ):
        # Integrate with sawyer so this line
        # comes from the actual template used
        FIRST_LINE_CHANGELOG_TEMPLATE = (
            '## [{{ current_tag }}](https://github.com/{{ owner }}'
            '/{{ repo }}/tree/{{ current_tag }})'
        )

        first_line_of_previous_release = jinja2_render(
            {
                'current_tag': last_tag,
                'owner': owner,
                'repo': repo
            },
            FIRST_LINE_CHANGELOG_TEMPLATE
        )

        release_changelog = ''
        with open(self.changelog_path) as changelog_file:
            for line in changelog_file:
                if first_line_of_previous_release in line:
                    break
                release_changelog += line

        return release_changelog
