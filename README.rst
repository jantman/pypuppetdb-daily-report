pypuppetdb_daily_report
=======================

.. image:: https://pypip.in/v/pypuppetdb-daily-report/badge.png
   :target: https://crate.io/packages/pypuppetdb-daily-report

.. image:: https://pypip.in/d/pypuppetdb-daily-report/badge.png
   :target: https://crate.io/packages/pypuppetdb-daily-report


.. image:: https://secure.travis-ci.org/jantman/pypuppetdb-daily-report.png?branch=master
   :target: http://travis-ci.org/jantman/pypuppetdb-daily-report
   :alt: travis-ci for master branch

.. image:: https://coveralls.io/repos/jantman/pypuppetdb-daily-report/badge.png?branch=master
   :target: https://coveralls.io/r/jantman/pypuppetdb-daily-report?branch=master
   :alt: coverage report for master branch

A daily run summary report for PuppetDB, written in Python using `nedap's pypuppetdb <https://github.com/nedap/pypuppetdb>`_ module.

For an example of the current version's output, see `https://rawgithub.com/jantman/pypuppetdb-daily-report/master/example_output.html <https://rawgithub.com/jantman/pypuppetdb-daily-report/master/example_output.html>`_.

The report displays the following for the current point-in-time:

* the current values of 'puppetversion', 'facterversion' and 'lsbdistdescription' facts

And the following for each day in the run interval:

* dashboard metrics (averages where possible) snapshotted at the time the script was run

* total number of runs, number of runs with failures

* number of nodes with:

  * no successful runs, 50+% failed runs, any failed runs

  * less than 40 successful runs in 24 hours

  * count of runs with changed resources

  * count of nodes with changed resources

* top 10 failing resources, along with count of nodes they're failing on

* top 10 resources changed, how many nodes and how many runs they were changed in

* any (up to 10) resources changed in at least 45% of runs on a node (flapping)


Development
===========

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests) (note that until
  https://github.com/lemurheavy/coveralls-public/issues/31 is fixed, you
  need to check the ``cov`` output for branch coverage, coveralls can't
  be relied on).

Testing
-------

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <http://tox.testrun.org/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox``

* If you want to see code coverage: ``tox -e cov``

  * this produces two coverage reports - a summary on STDOUT and a full report in the ``htmlcov/`` directory

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off master for that issue.
2. Confirm that there are CHANGES.rst entries for all major changes.
3. Ensure that Travis tests passing in all environments.
4. Ensure that test coverage is no less than the last release (ideally, 100%).
5. Increment the version number in __init__.py and add version and release date to CHANGES.rst, then push to GitHub.
6. Confirm that README.rst renders correctly on GitHub.
7. Upload package to testpypi, confirm that README.rst renders correctly.

   * Make sure your ~/.pypirc file is correct
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist upload -r https://testpypi.python.org/pypi``
   * Check that the README renders at https://testpypi.python.org/pypi/pypuppetdb-daily-report

8. Create a pull request for the release to be merge into master. Upon successful Travis build, merge it.
9. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -a vX.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin vX.Y.Z``

11. Upload package to live pypi:

    * ``python setup.py sdist upload``

10. make sure any GH issues fixed in the release were closed.
