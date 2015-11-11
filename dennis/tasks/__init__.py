from .prepare import PrepareTask, RELEASE_TYPES
from .release import ReleaseTask
from .utils import VERSION_REGEX, get_next_version_options

TASKS = {
    'prepare': PrepareTask,
    'release': ReleaseTask
}
