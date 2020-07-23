# Slack notifier

This project provides a simple command line tool that reads status check updates
from the Github API and posts or updates a Slack message.

## Usage

This script is intended to be run as part of a Github Workflow. Here's an example
workflow:

```yaml
name: Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v1
        with:
          python-version: 3.8
      - name: Download executable
        run: curl -sSL -o ./notifier "https://github.com/kolonialno/slack-notifier/releases/download/v1.0.0/notifier"
      - name: Run notifier
        run: ./notifier --repo ${{github.repo}} --slack-channel #my-channel --commit ${{github.sha1}}
        env:
          GITHUB_TOKEN: ${{secrets.GITHUB_TOKEN}}
          SLACK_TOKEN: ${{secrets.SLACK_TOKEN}}
```
