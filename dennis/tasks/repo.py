import os
import git


class DirectoryRepoProvider:

    project_dir = None

    def __init__(self, project_dir=os.getcwd()):
        self.project_dir = project_dir

    def get(self):
        return git.Repo(self.project_dir)
