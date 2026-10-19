# GitHub Secret Manager

[![Sync workflow](https://github.com/fopina/github-secret-manager-template/actions/workflows/sync-secrets.yml/badge.svg?branch=main)](https://github.com/fopina/github-secret-manager-template/actions/workflows/sync-secrets.yml)

GitHub lets an organization share Actions secrets across its repositories, but a personal account has no equivalent for repositories in your user-named space. This project fills that gap: it maps secrets to selected repositories and copies their values there. It is not as convenient as organization-wide secrets, but it gets close.

## Use it

1. Add each source value as an Actions secret in this repository. The source secret names are the keys in `mapping.yaml`.
2. [Create a fine-grained personal access token](https://github.com/settings/personal-access-tokens) and add it as `REPOSITORY_SECRETS_TOKEN`. Give it **Secrets: Read and write** access to the repositories it should update (or all your repositories), with no other permissions beyond GitHub's required Metadata read access.
3. Edit `mapping.yaml` with your target repositories. The current entries are examples; replace them with repositories you own. A target may use a different secret name with `name`.
4. Run **Sync repository secrets** manually from the Actions tab on the `main` branch.

The workflow validates the mapping and updates each listed repository. GitHub does not let it read existing target secret values, so syncing always copies the source value. Keep this repository and its workflow access restricted: anyone who can change and run the workflow may overwrite secrets in repositories the token can access.

The workflow uses GitHub's `github.repository_owner` value to ensure every target belongs to the account that owns this manager repository.
