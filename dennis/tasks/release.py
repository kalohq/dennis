import logging

from .task import Task

_log = logging.getLogger(__name__)


class ReleaseTask(Task):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        # Checkout and pull the release branch
        self._checkout_and_pull(
            self.meta['release_branch_name']
        )

        pr_id = self._get_pr_id()
        import pdb
        pdb.set_trace()

        # Publish release

        # Merge PR into master
        # ... this will say no until build has passed

        # Merge master into develop
