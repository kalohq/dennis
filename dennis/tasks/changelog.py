import requests
import logging
import dateutil.parser

from jinja2 import Environment, PackageLoader

from .task import Task


def render_changelog(context, template='default.md'):
    env = Environment(loader=PackageLoader('sawyer', 'templates'))
    template = env.get_template(template)

    return template.render(**context)


API_URI = 'https://api.github.com/repos/{owner}/{repo}'
_log = logging.getLogger(__name__)


class PullRequest:
    def __init__(self, data):
        self.number = data['number']
        self.title = data['title']
        self.url = data['url']
        self.created_at = dateutil.parser.parse(data['created_at'])
        if data['merged_at']:
            self.merged_at = dateutil.parser.parse(data['merged_at'])
        else:
            self.merged_at = None
        self.user = data['user']['login']
        self.state = data['state']
        self.raw = data

    @property
    def created_merged_delta(self):
        if self.merged_at:
            return self.merged_at - self.created_at

    def __str__(self):
        return 'Pull request #{number} by {user}'.format(
            number=self.number,
            user=self.user
        )


class GithubFetcher:
    def __init__(self, user, password, owner, repo):
        self.auth = user, password
        self.uri = API_URI.format(owner=owner, repo=repo) + self.endpoint

    @property
    def endpoint(self):
        """Endpoint to visit in the API."""
        raise NotImplementedError

    def fetch(self):
        """Method to fetch the API endpoint."""
        return requests.get(self.uri, auth=self.auth).json()


class PullRequestFetcher(GithubFetcher):
    endpoint = '/pulls'

    def _fetch_recursive(self, page, raw_prs=[]):
        params = {
            'state': 'all',
            'page': page,
            'direction': 'asc'
        }

        response = requests.get(
            self.uri, params=params, auth=self.auth
        )

        if response.status_code == 401:
            raise ValueError('Wrong password')

        raw = response.json()

        # Until no content is returned, get more PRs
        if raw:
            for item in raw:
                raw_prs.append(item)

            _log.info('Got {} pull requests'.format(len(raw_prs)))
            return self._fetch_recursive(page=page+1, raw_prs=raw_prs)
        else:
            return raw_prs

    def fetch(self):
        raw_prs = self._fetch_recursive(1)
        pull_requests = []
        for pr in raw_prs:
            pull_requests.append(PullRequest(pr))

        return pull_requests


class TagFetcher(GithubFetcher):
    endpoint = '/git/refs/tags'


class ChangelogTask(Task):

    def run(self):
        import pdb
        pdb.set_trace()

        pr_fetcher = PullRequestFetcher(
            self.github_user, self.github_token,
            self.repo.owner, self.repo.name
        )
        prs = pr_fetcher.fetch()

        commit = requests.get(
            url, auth=(self.github_user, self.github_token)
        ).json()

        field = 'author' if 'author' in commit else 'tagger'
        previous_date = dateutil.parser.parse(commit[field]['date'])

        merged_prs_since = sorted(
            [
                pr for pr in prs
                if (pr.merged_at and pr.merged_at > previous_date)
            ],
            key=lambda pr: pr.merged_at,
            reverse=True
        )

        context = {
            'current_tag': self.meta['release_tag'].name,
            'previous_tag': self.meta['last_tag'].name,
            'owner': self.repo.owner,
            'repo': self.repo.name,
            'pull_requests': merged_prs_since
        }

        print(render_changelog(context))
