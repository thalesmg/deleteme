#!/usr/bin/env python3

from github import Github
from github.CheckRun import CheckRun
from github.PullRequest import PullRequest
from github.Repository import Repository
from optparse import OptionParser
import os
import requests
from typing import Optional


def request_rerun(check_run: CheckRun, token: str, pr: PullRequest):
    """
    The GH lib currently doesn't support this action directly...
    """
    headers = {'Accept': 'application/vnd.github.v3+json',
               'User-Agent': 'python3',
               'Authorization': f'Bearer {token}'}
    url = f"{check_run.url}/rerequest"
    print("Request rerun for {pr}/{check_run}")
    resp = requests.post(url, headers=headers)
    if resp.status_code != 201:
        print(f"Rerun request to run failed for {pr}/{check_run}: {resp.status_code} {resp.content}")
    else:
        print(f"Rerun request succeeded for {pr}/{check_run}")


def list_open_master_prs(repo: Repository, base: str) -> list[PullRequest]:
    return [pr
            for pr in repo.get_pulls()
            if pr.base.ref == base]


def get_apps_version_check_run(repo: Repository, pr: PullRequest) -> Optional[CheckRun]:
    commit = repo.get_commit(pr.head.sha)
    crs = [cr
           for cr in commit.get_check_runs()
           if cr.name == 'check_apps_version']
    if crs:
        return crs[0]


def main():
    parser = OptionParser()
    parser.add_option("-r", "--repo", dest="repo",
                      help="github repo", default="emqx/emqx")
    parser.add_option("-t", "--token", dest="gh_token",
                      help="github API token")
    parser.add_option("-b", "--base", dest="base", default='master',
                      help="Base branch for PRs")
    (options, args) = parser.parse_args()

    # Get gh token from env var GITHUB_TOKEN if provided, else use the one from command line
    token = os.environ['GITHUB_TOKEN'] if 'GITHUB_TOKEN' in os.environ else options.gh_token

    gh = Github(token)
    repo = gh.get_repo(options.repo)
    open_prs = list_open_master_prs(repo, options.base)
    print("open prs", open_prs)
    apps_version_check_runs = [(cr, pr)
                               for pr in open_prs
                               if (cr := get_apps_version_check_run(repo, pr))]
    for cr, pr in apps_version_check_runs:
        request_rerun(cr, token, pr)


if __name__ == '__main__':
    main()
