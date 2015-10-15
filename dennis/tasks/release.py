import logging

from jinja2 import Template

from .task import Task

_log = logging.getLogger(__name__)


def jinja2_render(context, template_text):
    return Template(template_text).render(**context)


class ReleaseTask(Task):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

        pr_id = self._get_pr_id()

        release_pr = self.github_repo.get_pull(pr_id)

        import pdb
        pdb.set_trace()

        # Merge PR into master
        if release_pr.mergeable and not release_pr.is_merged():
            _log.info('Pull request "{}" in {} is mergeable, merging'.format(
                release_pr.title,
                self.repo_name
            ))
            self._merge(release_pr)

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
            self.meta['last_tag'].name, self.meta['release_tag_name'],
            self.repo_name.split('/')[-1], self.repo_owner
        )

        self.github_repo.create_git_tag_and_release(
            self.meta['release_tag_name'],
            '', release_pr.title,
            changelog, last_commit_id, 'commit',
            draft=self.draft, prerelease=self.draft
        )

        # Merge master into develop
        mergeback_pr = self.github_repo.create_pull(
            'Master back into Develop', '',
            'develop', 'master'
        )
        if mergeback_pr.mergeable:
            _log.info('Pull request "{}" in {} is mergeable, merging'.format(
                mergeback_pr.title,
                self.repo_name
            ))
            self._merge(mergeback_pr)

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
