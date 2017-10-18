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
        - Create GitHub release
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
                ' by re-running "dennis release" with the correct'
                ' "--type"'.format(self.repo_name)
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

        # Checkout release
        self._checkout_and_pull(self.release.name)

        # Get latest master commit ID
        self._checkout_and_pull('master')
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
                '', last_commit_id, 'commit',
                target_commitish=last_commit_id
            )
            github_release_url = release.raw_data['html_url']
            _log.info('GitHub release created')

        # Merge master into develop
        if not self.release.merged_back:
            self._merge_branches(
                'develop', 'master', '(dennis) Master back into Develop'
            )

        # Done
        _log.info(
            '{} is merged into master, and develop has'
            ' been updated. \n\nSee the latest published release @ {}'.format(
                format_release_pr_name(self.release.version),
                github_release_url)
        )
