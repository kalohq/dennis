# Dennis -- helping to release and ship it

## Setup

- It's advised you use a cache directory so Dennis doesn't need to clone the repositories for every release.

```
mkdir -p ~/.dennis
```

- You may benefit from either adding a Bash alias, or from creating a one-liner script within your project, for running the releases

```
# If you're using Bash
echo "# Dennis release helper" >> ~/.bash_profile
echo "alias dennis='docker run --rm -v ~/.dennis:/git -ti -e REPO=<repo name> -e OWNER=<owner name> lystable/dennis'" >> ~/.bash_profile
```

## [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow)-esque Use Cases

You may run the release commands from any directory. Dennis maintains its own cache of cloned repositories, on its mounted volume.

### Docker command

The command should always be run with these settings:

```
docker run -v ~/.dennis:/git -ti -e REPO=<repo name> -e OWNER=<owner name, defaults to lystable> lystable/dennis
```

which is why it's recommended either to create a Bash alias, or, if you have multiple repositories to manage, to have a script within each one of them.

Further down, we'll assume we have aliased the above options as 'dennis'.

### Create and Release a normal (minor) release
```
# Step 1
please dennis prepare --type minor --user <Github username> --token <Github token>
#
# ... QA cycle ...
#
# Step 2
please dennis release --type minor --user <Github username> --token <Github token>
```

### Create and Release a hotfix

```
# Step 1
# Publish a branch onto Github, make sure you created it from "master" and not from "develop"

# Step 2
please dennis prepare --type hotfix --user <Github username> --token <Github token> --branch <a published branch name>

#
# ... QA cycle ...
#

# Step 3
please dennis release --type hotfix --user <Github username> --token <Github token>
```

## Extras

- You'll be happy to hear that `dennis` acts in an idempotent fashion, so he'll try to pick up where he left off if there was a partial failure previously, for whatever reason
- `dennis` does allow to override the version number and source branch from which the release is created, e.g.:

```
please dennis prepare --version v53.69.999 --branch feature/please-avoid-this-dangerous-workflow
```

## License

Apache 2.0. See LICENSE for details
