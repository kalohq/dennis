from .prepare import PrepareTask, RELEASE_TYPES
from .release import ReleaseTask

TASKS = {
    'prepare': PrepareTask,
    'release': ReleaseTask
}
