# Dennis -- helping to release and ship it

## Quickstart

- Checkout and Install:

```
# Install sawyer manually (this needs fixing, probably a PR to sawyer)
git clone https://github.com/lystable/sawyer sawyer
cd sawyer
python3 setup.py develop

# Install dennis
git clone https://github.com/lystable/dennis dennis
cd dennis
python3 setup.py develop
```

You'll need to run any `dennis` commands from within the Git project you wish to release.

- Prepare a release:

```
dennis prepare --type minor --user <your username>
```

- Draft a release:

```
dennis release --type minor --user <your username> --draft
```

This will not merge any PRs, but it's useful for ensuring the current release state is retrieved normally.

- Complete a release:

```
dennis release --type minor --user <your username>
```

## [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow)-esque Use Cases

### Create and Release a normal (minor) release
```
# Step 1
dennis prepare --type minor --user yannispanousis
#
# ... QA cycle ...
#
# Step 2
dennis release --type minor --user yannispanousis
```

### Create and Release a hotfix

```
# Step 1
dennis prepare --type hotfix --user yannispanousis --branch <a published branch name>
#
# ... QA cycle ...
#
# Step 2
dennis release --type hotfix --user yannispanousis
```

**Please Note:** `dennis` doesn't validate that this provided branch is based off master (which it should be, for hotfixes, according to GitFlow). So you must carefully inspect the release PR you will be creating and make sure there are no unwanted changes.

## Extras

- You'll be happy to hear that `dennis` acts in an idempotent fashion, so he'll try to pick up where he left off if there was a partial failure previously, for whatever reason
- `dennis` does allow to override the version number and source branch from which the release is created, e.g.:

```
dennis prepare --version v53.69.999 --branch feature/please-avoid-this-dangerous-workflow
```
