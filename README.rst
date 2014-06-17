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

A daily run summary report for PuppetDB, written in Python using nedap's pypuppetdb module.

The report displays the following for the current point-in-time:

* the current values of 'puppetversion', 'facterversion' and 'lsbdistdescription' facts

And the following for each day in the run interval:

* dashboard metrics (averages where possible) snapshotted at the time the script was run

* total number of runs, number of runs with failures

* number of nodes with:

  * no successful runs, 50+% failed runs, any failed runs

  * less than X successful runs in 24 hours (default 40, CLI option)

  * count of runs with changed resources

  * count of nodes with changed resources

* top 10 failing resources, along with count of nodes they're failing on

* top 10 modules causing failures

* top 10 resources changed, how many nodes and how many runs they were changed in

* any (up to 10) resources changed in at least 45% of runs on a node (flapping)
