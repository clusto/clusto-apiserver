Releasing a new version
=======================

Once you are comfortable with the changes to be released, there is a few
things you have to do to consider this software "released".

It is worth mentioning that I will very probably script all (or almost all)
of this, once I have the time / decide how to do it.


Pre-requisites
--------------

* You need a github account with permissions for pushing new tags/releases
* You need to be added to the PyPi project so you can submit new releases
* Your ``~/.pypirc`` is configured with your PyPi username and password
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

This entails publishing the release on github. Once you publish the release on
github, a tweet will be posted shortly (< 1 hour after) to the @clustodotorg
account.

#.  *Push your changes up to the repo*: You need to both ``git push`` and
    ``git push --tags`` for this operation, your changes should be visible now,
    and the new tag should appear in https://github.com/clusto/clusto-apiserver/tags
#.  *Edit the tag so it turns into a release in github*: Draft a new release
    https://github.com/clusto/clusto-apiserver/releases/new and pick the tag
    you recently created. The title of the release should be "Version 0.0.1"
    (to continue with the sample version) and the body should be the contents
    of the ``docs/changelog/v0.0.1.rst`` file. Keep in mind that the format
    is Markdown while the documentation is ReStructured Text, so adjust as
    necessary (mainly titles change i.e. replace ``^`` for ``-``)

At this point the release should appear in the github releases page
https://github.com/clusto/clusto-apiserver/releases/


Uploading to PyPi
-----------------

Finally, publishing the module / source code to PyPi should be a single step:

*   *Sign and upload the new version tarball*: Basically run (from the project's
    root dir)::

        python setup.py sdist upload --sign [--identity <GPG identity>]

    What this does is:

    #.  Creates a tarball under the ``dist/`` directory (the ``sdist`` command)
    #.  Using the ``--sign`` flag signs the tarball using your GPG key (depending
        on your setup, you may get prompted for your GPG password). Optionally,
        you can use the ``--identity`` argument if you aren't using your default
        identity to sign
    #.  Uploads the recently created and signed tarball to PyPi (the ``upload``
        command)

At this point, the new version should be visible in https://pypi.python.org/pypi/clusto-apiserver

