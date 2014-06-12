pypuppetdb_daily_report
=======================

A daily run summary report for PuppetDB, written in Python using nedap's pypuppetdb module.

To Do
------

The final plan is something like this:

* should store configuration in a class, so there's an easy way to plug in a config file later

* get all of the data from the API. we want to grab current dashboard metrics, and then everything about nodes/runs/etc.

* the metric gathering should incorporate caching - i.e. we request metrics for a given day (today or a day in the past),
  first we check to see if there's a JSON cache file on disk. If not, we get from the API and write the cache file with
  the raw data

* should automatically purge cache files older than the run interval, unless --no-purge-cache

* should cache to disk at a default path, like /tmp/pypuppetdb_daily_report. Have an option to change that path, or optionally
  (i.e. with a value like "none") disable all caching (don't touch the cache at all)

* first version should display the following for today and the last N days:

  * the current values of 'puppetversion' and 'facterversion' facts for today

  * perhaps a summary of client OSes

  * dashboard metrics (averages where possible)

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
