"""Validate mapping.yaml and turn each secret destination into a matrix job."""

import json
import os
import re

import yaml


SECRET_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def fail(message):
    raise SystemExit(f"Invalid mapping.yaml: {message}")


def is_valid_secret_name(name):
    return (
        isinstance(name, str)
        and SECRET_NAME_PATTERN.fullmatch(name) is not None
        and not name.upper().startswith("GITHUB_")
    )


def read_mapping():
    try:
        with open("mapping.yaml", encoding="utf-8") as mapping_file:
            document = yaml.safe_load(mapping_file)
    except (OSError, yaml.YAMLError) as error:
        fail(str(error))

    if (
        not isinstance(document, dict)
        or not set(document).issubset({"secrets", "groups"})
        or not document
    ):
        fail("expected top-level 'secrets' and/or 'groups' mappings")

    secrets = document.get("secrets", {})
    groups = document.get("groups", {})
    if not isinstance(secrets, dict):
        fail("'secrets' must be a mapping")
    if not isinstance(groups, dict):
        fail("'groups' must be a mapping")
    if not secrets and not groups:
        fail("'secrets' and 'groups' cannot both be empty")

    return secrets, groups


def build_entries(secrets, groups):
    entries = []
    repository_owner = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not repository_owner:
        fail("GITHUB_REPOSITORY_OWNER is not set")

    def add_targets(source_name, targets, context):
        if not is_valid_secret_name(source_name):
            fail(f"invalid source secret name: {source_name!r}")

        if not isinstance(targets, list) or not targets:
            fail(f"{context}.targets must be a non-empty list")

        for target in targets:
            if (
                not isinstance(target, dict)
                or not set(target).issubset({"repository", "name"})
                or "repository" not in target
            ):
                fail(
                    f"each {context} target must contain 'repository' "
                    "and optionally 'name'"
                )

            repository = target["repository"]
            if not isinstance(repository, str) or REPOSITORY_PATTERN.fullmatch(repository) is None:
                fail(f"invalid target repository: {repository!r}")
            target_owner = repository.split("/", 1)[0]
            if target_owner.casefold() != repository_owner.casefold():
                fail(
                    f"target repositories must be owned by "
                    f"{repository_owner}: {repository!r}"
                )

            target_name = target.get("name", source_name)
            if not is_valid_secret_name(target_name):
                fail(f"invalid target secret name: {target_name!r}")

            entries.append(
                {
                    "source": source_name,
                    "repository": repository,
                    "name": target_name,
                }
            )

    for source_name, config in secrets.items():
        if not isinstance(config, dict) or set(config) != {"targets"}:
            fail(f"{source_name} must contain only a 'targets' list")
        add_targets(source_name, config["targets"], source_name)

    for group_name, config in groups.items():
        if (
            not isinstance(group_name, str)
            or not group_name
            or not isinstance(config, dict)
            or set(config) != {"secrets", "targets"}
        ):
            fail(f"group {group_name!r} must contain only 'secrets' and 'targets'")

        source_names = config["secrets"]
        if (
            not isinstance(source_names, list)
            or not source_names
            or any(not is_valid_secret_name(name) for name in source_names)
            or len(set(source_names)) != len(source_names)
        ):
            fail(f"groups.{group_name}.secrets must be a non-empty list of unique names")

        for source_name in source_names:
            add_targets(source_name, config["targets"], f"groups.{group_name}")

    return entries


def main():
    matrix = {"include": build_entries(*read_mapping())}
    print(f"matrix={json.dumps(matrix, separators=(',', ':'))}")


if __name__ == "__main__":
    main()
