from .prepare import PrepareTask, RELEASE_TYPES
from .release import ReleaseTask
from .utils import VERSION_REGEX

TASKS = {
    'prepare': PrepareTask,
    'release': ReleaseTask
}
