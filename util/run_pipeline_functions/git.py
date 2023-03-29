import re
import subprocess

# Pull the latest pipeline
def pull_latest_pipeline(work_dir):
  git_process = subprocess.Popen(
      ['git', '-C', work_dir, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  git_process.wait()

# Extract a repository name from git URL
def get_repo_name(git_url):
  repo_name = re.findall(r'.*/(.*?).git$', git_url)
  repo_name = repo_name[0] if len(repo_name) > 0 else None
  return(repo_name)

# Get the commit id of the latest Snakefile version.
def get_latest_commit_id(git_url):
  git_process = subprocess.Popen(
      ["git", "ls-remote", git_url], stdout=subprocess.PIPE)
  stdout, std_err = git_process.communicate()
  git_sha = re.split(r'\t+', stdout.decode('ascii'))[0]
  return(git_sha)