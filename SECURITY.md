# Security

Report credential exposure or a build-pipeline vulnerability privately to the
project lead. Add a private contact method here before publishing the
repository.

Never include a Crowdin token in source, workflow YAML, issues, logs, or pull
requests. Store it as the GitHub Actions secret `CROWDIN_PERSONAL_TOKEN`.
Revoke and replace a token immediately if it is exposed.

The self-hosted build runner contains a licensed game installation. Restrict it
to trusted maintainers and tag/manual workflows; do not expose it to fork pull
requests.
