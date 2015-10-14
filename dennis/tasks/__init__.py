from .prepare import PrepareTask, RELEASE_TYPES
from .release import ReleaseTask
from .changelog import ChangelogTask

TASKS = {
    'prepare': PrepareTask,
    'release': ReleaseTask,
    'changelog': ChangelogTask
}
