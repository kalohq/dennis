# Dennis -- helping to release and ship it

## Quickstart

- Checkout and Install:

```
# Fix this issue (probably a PR to sawyer)
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
