import git

class GitDiffParser:
  """Parser using git diff to extract and parse file diffs"""

  def __init__(self, repo_path: str="."):
    self.repo = git.Repo(repo_path)
    print(self.repo.git.diff())