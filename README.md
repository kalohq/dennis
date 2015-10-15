# Dennis -- helping to release and ship it

## Quickstart

Checkout and Install:

```
git clone https://github.com/lystable/dennis dennis
cd dennis
sudo python3 setup.py develop
```

You'll need to run any `dennis` commands from within the Git project you wish to release.

Prepare a release:

```
dennis prepare --type fix --user <your username>
```

Complete a release:

```
dennis release --user <your username>
```
