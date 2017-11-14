import logging

from jinja2 import Template

from .task import Task
from .utils import format_release_pr_name
from git.exc import GitCommandError

_log = logging.getLogger(__name__)


def jinja2_render(context, template_text):
    return Template(template_text).render(**context)


class ReleaseTask(Task):
    """
        Steps:

        - If no ongoing release, exit
        - Merge release PR into master if build passes
        - Checkout and pull release branch
        - Merge master back into develop

    """

    wait_for_minutes = 0

    def __init__(self, wait_for_minutes=0, **kwargs):
        super().__init__(**kwargs)
        self.wait_for_minutes = wait_for_minutes

    def run(self):
        if not self.release:
            _log.warn(
                'Could not find an ongoing {} release for {}.'
                ' Perhaps you haven\'t run "dennis prepare" yet?'
                .format(self.version_type, self.repo_name)
            )
            _log.warn(
                '\n\n\n'
                'Alternatively, if you meant a different release type,'
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

        # Merge master into develop
        _log.info('\t- is release merged back into develop...')
        last_commit = (
            self.repo.remotes.origin.fetch(refspec='master')[0].commit.hexsha
        )
        if not self._branch_contains_commit('develop', last_commit):
            self._merge_branches(
                'develop', 'master', '(dennis) Master back into Develop'
            )

        # Switch back to develop
        self._checkout_and_pull('develop')

        # Delete release branch
        _log.info('Deleting release branch')

        try:
            self.repo.delete_head(self.release.name)
        except GitCommandError:
            _log.info(
                'Nothing to delete locally, release branch wasn’t present'
            )

        try:
            self.repo.remotes.origin.push(':{}'.format(self.release.name))
        except GitCommandError:
            _log.info(
                'Nothing to delete remotely, release branch wasn’t present'
            )

        # Done
        _log.info(
            'Your {} release is merged into master and develop has been'
            ' updated.'.format(
                format_release_pr_name(self.release.version_type),
            )
        )
