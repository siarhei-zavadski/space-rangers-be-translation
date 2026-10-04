# Security

Report credential exposure or a build-pipeline vulnerability privately to the
project lead. Add a private contact method here before publishing the
repository.

Never include a Crowdin token in source, workflow YAML, issues, logs, or pull
requests. Store it as the GitHub Actions secret `CROWDIN_PERSONAL_TOKEN`.
Revoke and replace a token immediately if it is exposed.

The self-hosted build runner is a maintainer's Linux machine with a licensed
Space Rangers HD installation. The game stays on that disk. GitHub-hosted
runners must not receive those files.

`Build mod` may run only from a manual `workflow_dispatch` or a `v*` tag,
and only on the labels `self-hosted`, `linux`, and `space-rangers-hd`. Do not
add `pull_request`, `pull_request_target`, or `workflow_run` to that workflow.

The repository is public, so a fork pull request can replace a workflow and
select that same machine. In Settings → Actions → General, require approval
for all outside collaborators before fork workflows run. Approval still runs
the fork's workflow on the runner, so read workflow changes before approving
them. Do not keep other credentials on the machine.
