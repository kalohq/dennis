# Dennis -- helping to release and ship it

## Install

- This is **recommended** to be installed inside a [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) and loaded using [virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/en/latest/install.html#basic-installation), like this:
```
# Install virtualenv
pip install virtualenv virtualenvwrapper
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc

# Create a virtualenv for Dennis
mkvirtualenv -p python3.5 "dennis"
workon dennis

# Install sawyer
git clone https://github.com/lystable/sawyer sawyer
cd sawyer
python setup.py develop

# Install or Upgrade dennis
pip install -U GitflowDennis
```

## [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow)-esque Use Cases

**You'll need to run any `dennis` commands from within the Git project you wish to release.**

### Create and Release a normal (minor) release
```
# Step 1
dennis prepare --type minor --user <Github username> --token <Github token>
#
# ... QA cycle ...
#
# Step 2
dennis release --type minor --user <Github username> --token <Github token>
```

### Create and Release a hotfix

```
# Step 1
# Make sure you created your hotfix branch from "master" and not from "develop"

# Step 2
dennis prepare --type hotfix --user <Github username> --token <Github token> --branch <a published branch name>

#
# ... QA cycle ...
#

# Step 3
dennis release --type hotfix --user <Github username> --token <Github token>
```

**Please Note:** `dennis` doesn't validate that this provided branch is based off master (which it should be, for hotfixes, according to GitFlow). So you must carefully inspect the release PR you will be creating and make sure there are no unwanted changes.

## Extras

- You'll be happy to hear that `dennis` acts in an idempotent fashion, so he'll try to pick up where he left off if there was a partial failure previously, for whatever reason
- `dennis` does allow to override the version number and source branch from which the release is created, e.g.:

```
dennis prepare --version v53.69.999 --branch feature/please-avoid-this-dangerous-workflow
```

# PyPI Update

Having followed this [guide](http://peterdowns.com/posts/first-time-with-pypi.html)

## Test

```
python setup.py sdist upload -r pypitest
```

## Real

```
python setup.py sdist upload -r pypi
```

## License

Apache 2.0. See LICENSE for details
