# Releases

## Release process

In the following order, at the end of a sprint, the release manager will:

* Merge all pending pull requests when possible, and for each corresponding card in Jira set the "Fix Version" field accordingly as well as change the status to "Waiting deploy"

* Ensure that the migration scripts are complete and working (see [upgrade-scripts.md](upgrade-scripts.md#run-a-version-upgrade-again) on how to execute a specific version scripts).
  
* For projects already used in Production, ensure migration is working in FULL mode. (see [how-to-use-a-prod-db-in-dev.md](how-to-use-a-prod-db-in-dev.md) to get a dump for projects hosted on cloud platform). 

* Increase the version number (see [invoke.md](invoke.md#releasebump) for more information)

  ```bash
  invoke release.bump --feature  # increment y number in x.y.z
  # or --patch to increment z number in x.y.z
  ```

* The "bump" command also pushes the pending-merge branches to a new branch named after the tag (`pending-merge-<project-id>-<version>`), if needed, this push can be manually called again with

  ```bash
  invoke release.push-branches
  ```

* Do the verifications: migration scripts, [changelog](../HISTORY.rst) (remove empty sections, ...)

* Commit the changes to [changelog](../HISTORY.rst), VERSION, ... on master with message 'Release x.y.z'

* Add a tag with the new version number, copying the changelog information in the tag description

  ```
  git tag -a x.y.z  # here, copy the changelog in the annotated tag
  git push --tags && git push
  ```

When the tag is pushed on GitHub, Travis will build a new Docker image (as
long as the build is green!) and push it on the registry as `camptocamp/geo_11_odoo:x.y.z`

If everything went well it is worth informing the project manager that a new release is ready to be tested on the Minions.

## Versioning pattern

The version is in the form `x.y.z` where:

* **x** is the major number, always equal to the Odoo version (9.x.z)
* **y** is the minor number, incremented at the end of each sprint, this is
  were new features are added
* **z** is the patch number, incremented for corrections on production releases.

All the developments are done on the `master` branch and a new release on
`master` implies a new `minor` version increment.
When there is an issue with a released image after the tag has been set, a
patch branch is created from the tag and a new release is done from this
branch; the patch number is incremented.

## Patch process

### Quick checklist

1. Create a branch `patch-x.y.next-z` based from the source tag `x.y.z` to 
   correct
2. Push the branch to the camptocamp repository
3. Create a working branch based on `patch-x.y.next-z` which include your fix
4. Push your working branch on your fork repository and create a pull request 
   on `patch-x.y.next-z`
5. Ask for reviews, get reviewed, merge
6. Create a release `x.y.next-z`
7. **Merge the branch `patch-x.y.next-z` in master (very important to have the 
   fix for the next release!)**

You can refer to the more detailed documentation below.

### Short story

Example of branches involving Paul as the Release manager and Liza and Greg as
developers, the current version is `9.3.2`:

* Liza works on a new feature so she creates a branch for master:

    ```
    git checkout origin/master -b impl-stock-split
    git push liza/impl-stock-split
    ```

* Greg works on a new feature too:
    ```
    git checkout origin/master -b impl-crm-claim-email
    git push greg/impl-crm-claim-email
    ```
* The end of sprint is close, both propose their branches as pull requests in
    `master`, builds are green!
* Paul merges the pull requests, prepares a new release and when he's done, he
    tags `master` with `9.4.0`
* Paul tests the image `camptocamp/geo_11_odoo:9.4.0` and oops, it seems he
    goofed as the image doesn't even start
* Paul corrects the - hopefully - minor issue and prepare a new release for
    `9.4.1`.
* Liza works on another shiny feature:
    ```
    git checkout origin/master -b impl-blue-css
    git push liza/impl-blue-css
    ```
* And Greg is assigned to fix a bug on the production server (now in `9.4.1`),
    so he will do 2 things:
    * create a patch branch **from** the production version:
        ```
        git checkout 9.4.1 -b patch-claim-typo
        git push greg/patch-claim-typo
        ```
    * ask Paul to create a new patch branch `patch-9.4.2`, on which he will
        propose his pull request
* Paul prepare a new release on the `patch-9.4.2` branch. Once released, Paul merges `patch-9.4.2` in `master`.
* At the end of the sprint, Paul prepares the next release `9.5.0` with the new Liza's feature and so on.

### Detailed instruction

1. Create remote patch branch

    * Figure out target version `number` in format `x.y.z` (`9.4.0`) for which
        you need to make patch. It can be version released on production or
        integration or specified by PM. Or maybe other case.
    * Create patch branch from target with name `patch-x.y.next_z`
        (`patch-9.4.1`). Where `next_z = z + 1` (`1 = 0 + 1`).
        ```git
        git checkout x.y.z -b patch-x.y.next_z
        ```
        example
        ```git
        git checkout 9.4.0 -b patch-9.4.1
        ```
    * Push new empty branch to repo.
        ```git
        git push origin patch-x.y.next_z
        ```
        example
        ```git
        git push origin patch-9.4.1
        ```
        Where `origin` should be camptocamp project repo

    Alternative you can create `patch-x.y.next_z` branch on github directly.

2. Create local patch branch

    * Create your local patch branch.
    * Do required changes for patch.
    * Commit your changes.
    * Push your changes to your remote fork repo.
    * Create PR to patch remote project branch.
        ```git
        camptocamp/geo_11/patch-x.y.next_z <- <user_name>/geo_11/<your_patch_branch>
        ```
    * Request PR review in chat to speedup merge.
    * Merge after reviewers approve your changes.

3. Create patch release

    * After merge your PR to remote patch-branch do release.
        Your current branch should be `patch-x.y.next_z`.
        See [Release process](#release-process) section.

4. **Merge patch-branch to master**

    * **Merge `patch-x.y.next_z` to `master` to incorporate patch changes
        into master branch.**
