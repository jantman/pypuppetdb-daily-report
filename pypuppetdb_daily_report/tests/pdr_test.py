"""
tests for pypuppetdb_daily_report

The latest version of this package is available at:
<https://github.com/jantman/pypuppetdb-daily-report>

It is highly recommended that you install this via `pip`.

##################################################################################
Copyright 2013 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of pypuppetdb-daily-report.

    pypuppetdb-puppet-report is licensed under the Apache License version 2.0.
    please see LICENSE file for full text.
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/pypuppetdb-daily-report> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

"""

import pytest
import sys
import os
import shutil

from pypuppetdb_daily_report import pypuppetdb_daily_report as pdr


class OptionsObject(object):
    """
    object to mock optparse return object
    """

    def __init__(self):
        """
        preseed with default values
        """
        self.dry_run = False
        self.verbose = 0
        self.host = None
        self.num_days = 7


class TestOptions:
    """
    Tests the CLI option/argument handling
    """

    def test_defaults(self):
        """
        Test the parse_args option parsing method with default / no arguments
        """
        argv = ['pypuppetdb_daily_report']
        x = pdr.parse_args(argv)
        assert x.dry_run == False
        assert x.verbose == 0

    def test_dryrun(self):
        """
        Test the parse_args option parsing method with dry-run specified
        """
        argv = ['pypuppetdb_daily_report', '-d']
        x = pdr.parse_args(argv)
        assert x.dry_run == True
        argv = ['pypuppetdb_daily_report', '--dry-run']
        x = pdr.parse_args(argv)
        assert x.dry_run == True

    def test_verbose(self):
        """
        Test the parse_opts option parsing method with verbose specified
        """
        argv = ['pypuppetdb_daily_report', '-v']
        x = pdr.parse_args(argv)
        assert x.verbose == 1

    def test_debug(self):
        """
        Test the parse_opts option parsing method with debug specified
        """
        argv = ['pypuppetdb_daily_report', '-vv']
        x = pdr.parse_args(argv)
        assert x.verbose == 2

    def test_host(self):
        """
        Test the parse_opts option parsing method with a PuppetDB URL
        """
        argv = ['pypuppetdb_daily_report', '-p', 'foobar']
        x = pdr.parse_args(argv)
        assert x.host == 'foobar'
        argv = ['pypuppetdb_daily_report', '--puppetdb', 'foobar']
        x = pdr.parse_args(argv)
        assert x.host == 'foobar'

    def test_num_days(self):
        """
        Test the parse_opts option parsing method with number of days specified
        """
        argv = ['pypuppetdb_daily_report', '-n', '14']
        x = pdr.parse_args(argv)
        assert x.num_days == 14
