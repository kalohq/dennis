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
dennis prepare --type fix --user <your username>
```

- Draft a release:

```
dennis release --user <your username> --draft
```

This will not merge any PRs, but it's useful for ensuring the current release state is retrieved normally.

- Complete a release:

```
dennis release --user <your username>
```

## Extras

- You'll be happy to hear that `dennis` acts in an idempotent fashion, so he'll try to pick up where he left off if there was a partial failure previously, for whatever reason
- `dennis` does allow to override the version number and source branch from which the release is created, e.g.:

```
dennis prepare --version v53.69.999 --branch feature/please-avoid-this-dangerous-workflow
```
