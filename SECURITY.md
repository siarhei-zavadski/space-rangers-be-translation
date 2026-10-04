# Security

Report credential exposure or a build-pipeline vulnerability to the project lead.

Never include a Crowdin token in source, workflow YAML, issues, logs, or pull
requests. Revoke and replace a token immediately if it is exposed.

Builds that need the game run on a maintainer's machine, outside GitHub
Actions. Do not register a self-hosted runner for this public repository: a
fork pull request can send a job to any runner registered here. If a runner
is already registered, remove it under Settings → Actions → Runners and stop
the agent on that machine. GitHub-hosted runners must not receive the game
files.
