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
        self.verify = False
        self.config_file = None
        self.testfile = None
        self.ignorettl = False
        self.sleep = None


class TestSetup:
    """
    Tests the configuration/option handling and CLI functions
    """

    def test_options(self, monkeypatch):
        """
        Test the parse_opts option parsing method
        """
        def mockreturn(options):
            assert options.verify == True
            assert options.config_file == "configfile"
            assert options.testfile == "mytestfile"
            assert options.ignorettl == False
        monkeypatch.setattr(pdr, "parse_args", mockreturn)
        sys.argv = ['pydnstest', '-c', 'configfile', '-f', 'mytestfile', '-V']
        x = pdr.parse_args()

