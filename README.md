# Dennis -- helping to release and ship it

## [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow)-esque Use Cases

**You'll need to run any `dennis` commands from within the Git project you wish to release.**

### Create and Release a normal (minor) release
```
# Step 1
docker run --rm -v $PWD:/git lystable/dennis prepare --type minor --user <Github username> --token <Github token>
#
# ... QA cycle ...
#
# Step 2
docker run --rm -v $PWD:/git lystable/dennis release --type minor --user <Github username> --token <Github token>
```

### Create and Release a hotfix

```
# Step 1
# Make sure you created your hotfix branch from "master" and not from "develop"

# Step 2
docker run --rm -v $PWD:/git lystable/dennis prepare --type hotfix --user <Github username> --token <Github token> --branch <a published branch name>

#
# ... QA cycle ...
#

# Step 3
docker run --rm -v $PWD:/git lystable/dennis release --type hotfix --user <Github username> --token <Github token>
```

**Please Note:** `dennis` doesn't validate that this provided branch is based off master (which it should be, for hotfixes, according to GitFlow). So you must carefully inspect the release PR you will be creating and make sure there are no unwanted changes.

## Extras

- You'll be happy to hear that `dennis` acts in an idempotent fashion, so he'll try to pick up where he left off if there was a partial failure previously, for whatever reason
- `dennis` does allow to override the version number and source branch from which the release is created, e.g.:

```
docker run --rm -v $PWD:/git lystable/dennis prepare --version v53.69.999 --branch feature/please-avoid-this-dangerous-workflow
```

## License

Apache 2.0. See LICENSE for details
