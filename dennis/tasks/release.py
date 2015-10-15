import logging

from jinja2 import Template

from .task import Task

_log = logging.getLogger(__name__)


def jinja2_render(context, template_text):
    return Template(template_text).render(**context)


class ReleaseTask(Task):

    wait_for_minutes = 0

    def __init__(self, wait_for_minutes=0, **kwargs):
        super().__init__(**kwargs)
        self.wait_for_minutes = wait_for_minutes

    def run(self):
        # Is there a release?
        if not self.meta['release_branch_name']:
            _log.error('Could not find any ongoing release for {}'.format(
                self.repo_name
            ))
            return

        # Checkout and pull the release branch
        self._checkout_and_pull(
            self.meta['release_branch_name']
        )

        release_pr = self.meta['release_pr']

        # Merge PR into master
        if not release_pr.is_merged():
            _log.info('Pull request "{}" in {} is mergeable, merging'.format(
                release_pr.title,
                self.repo_name
            ))
            self._merge(release_pr, wait_for_minutes=self.wait_for_minutes)

        # Publish release
        #
        # Method Signature (thanks for the docs @PyGithub)
        #
        # create_git_tag_and_release(
        #    self, tag, tag_message, release_name, release_message, object,
        #    type, tagger=github.GithubObject.NotSet,
        #    draft=False, prerelease=False
        # ):
        last_commit_id = self.repo.heads.master.commit.hexsha
        changelog = self._get_release_changelog(
            self.meta['last_tag_name'], self.meta['release_tag_name'],
            self.repo_name, self.repo_owner
        )

        # Not making releases draft-able as this introduces complication
        # when handling the real release
        release_url = 'N/A'
        if (
            not self.meta['release'] and
            not self.draft
        ):
            release = self.github_repo.create_git_tag_and_release(
                self.meta['release_tag_name'],
                '', release_pr.title,
                changelog, last_commit_id, 'commit'
            )
            release_url = release.raw_data['html_url']

        # Merge master into develop
        self._merge_branches(
            'develop', 'master', '(dennis) Master back into Develop'
        )

        # Done
        _log.info(
            '{} is merged into master, and develop has'
            ' been updated. \n\nSee the latest published release @ {}'.format(
                release_pr.title,
                release_url)
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
