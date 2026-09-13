# Crowdin open-source readiness

Audit date: 2026-09-13.

## Current conclusion

This project is staged in the private
[`sergey-zavadsky/space-rangers-be-translation`](https://github.com/sergey-zavadsky/space-rangers-be-translation)
repository, but a private repository is **not eligible** for Crowdin's free
open-source license. Do not submit the application yet.

Crowdin currently requires all of the following:

| Requirement | Current evidence | Status |
|---|---|---|
| Crowdin project exists | <https://crowdin.com/project/space-rangers-hd-belarusian> | Ready |
| OSI-approved project license | Root `LICENSE` is MIT for original work | Ready, scope-limited |
| Source publicly downloadable | GitHub repository is private | **Blocked** |
| No related commercial product | Project is documented as a non-commercial fan mod | Confirm before applying |
| Applicant is project lead | Must be attested by the repository owner | Owner action |
| At least three months of work | No public Git history exists yet | **Blocked until evidenced** |
| Active collaborator community | No public contributor history exists yet | **Blocked** |
| Current website News section | `NEWS.md` is prepared; no public site exists | Blocked until published |
| Regular updated builds | Tag/release workflow is prepared; no release history exists | Blocked until established |
| Global TM/beta terms accepted | Must be accepted on the application form | Owner action |

Authoritative criteria:
<https://crowdin.com/product/for-open-source>.

## Rights gate before making the repository public

The scripts and contributor-authored text can be offered under MIT, but that
does not relicense Space Rangers' Russian/English source text or assets.
`crowdin/**/*.tsv` contains extracted source phrases. The game
[EULA](https://store.steampowered.com/eula/214730_eula_0) permits
non-commercial modding while restricting redistribution of proprietary
content.

Before changing repository visibility to public, obtain written permission
from the relevant rights holder to publish the extracted source corpus and
host it in Crowdin. Keep that permission in a private project-lead archive and
summarize its scope publicly. If permission is denied, keep the repository and
Crowdin project private/paid; an open-source license application would not be
appropriate.

The pinned `ranger-tools` upstream currently declares no license on GitHub. It
is not vendored here, but public/release use should still be cleared with its
author or replaced by a clearly licensed equivalent.

Suggested request:

> We maintain a free, non-commercial Belarusian translation mod for Space
> Rangers HD: A War Apart. May we publicly host the Russian source strings
> required for translation in a GitHub repository and Crowdin, and distribute
> the resulting translation mod? The repository will not contain the game,
> unmodified binary assets, or standalone playable content.

## Private GitHub staging checklist

1. **Done:** private repository created with `main` as its default branch.
2. **Done:** reviewed files pushed; `.gitignore` excludes game backups, the
   local environment, generated packages, and binary assets.
3. Revoke the previously shared Crowdin token, create a fresh least-privilege
   token, and add it as the Actions secret `CROWDIN_PERSONAL_TOKEN`. Project ID `930019` is
   non-secret and is already in the workflow/configuration.
4. Add the Actions repository variable `CROWDIN_SYNC_ENABLED=true` only after
   the replacement secret is present.
5. In **Settings → Actions → General**, allow GitHub Actions to create and
   approve pull requests.
6. Protect `main`; require the **Validate / corpus** check and pull requests.
7. For automated mod builds, register a trusted Linux self-hosted runner with
   the label `space-rangers-hd` and a legitimate game installation. Never run
   that workflow for untrusted pull requests.
8. Run **Crowdin sync** manually with `direction=both`; verify the generated
   translation PR before enabling the daily schedule.

Suggested GitHub metadata:

- Description: `Non-commercial classical Belarusian translation of Space Rangers HD`
- Website: `https://crowdin.com/project/space-rangers-hd-belarusian`
- Topics: `belarusian`, `taraskievica`, `translation`, `crowdin`, `game-mod`
- Initial visibility: `private`

## Path to an eligible application

1. Resolve the rights gate above.
2. Make the repository public.
3. Keep the MIT scope and third-party exclusions clear.
4. Record at least three months of genuine development in public commits.
5. Recruit and credit active collaborators through GitHub and Crowdin.
6. Update `NEWS.md` for meaningful changes.
7. publish tagged mod builds regularly using the prepared release workflow.
8. Replace the placeholders below, then submit Crowdin's request form.

Application facts to gather:

- Project lead name and Crowdin account: **TODO by owner**
- Public repository URL: **TODO; current repository is private**
- Project website/news URL: **TODO**
- First public development date (at least three months old): **TODO**
- Contributor evidence: **TODO**
- Recent release URLs and cadence: **TODO**
- Rights-holder permission reference: **TODO**
- Non-commercial declaration: **TODO by owner**

No CI configuration or repository metadata can substitute for these factual
eligibility requirements.
