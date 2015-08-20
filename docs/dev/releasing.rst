Releasing a new version
=======================

Once you are comfortable with the changes to be released, there is a few
things you have to do to consider this software "released"


Pre-requisites
--------------

* You need a github account with permissions for pushing new tags/releases
* You need to be added to the PyPi project so you can submit new releases
* You need your GPG key signed by one of the other maintainers


Cutting the release
-------------------

Usually involves a few steps (for simplicity, using version 0.0.1 to illustrate
the examples)

#.  *Updating the changelog*: You create a new page in ``docs/changelog``
    named ``docs/changelog/v0.0.1.rst``
#.  *Re-linking current changelog to new changelog*: You re-point the symlink
    from ``docs/changelog/current.rst`` to ``docs/changelog/v0.0.1.rst``
#.  *Commit your changelog change*
#.  *Update the version*: Need to bump the version in ``clustoapi/__init__.py``
    to reflect the new 0.0.1 version
#.  *Commit your version bump change*
#.  *Tag the release*: You need to ``git tag -s v0.0.1`` at this point. Pay
    attention to the ``-s`` switch, this implies the tag will be signed with
    your GPG key (optionally, use ``-u`` to specify which key to use if you
    don't want to use the default)


Publishing the release
----------------------

#.  *Push your changes up to the repo*: You need to both ``git push`` and
    ``git push --tags`` for this operation, your changes should be visible now,
    and the new tag should appear in https://github.com/clusto/clusto-apiserver/tags
