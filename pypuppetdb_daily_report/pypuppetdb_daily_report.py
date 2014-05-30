#!/usr/bin/env python
"""
pypuppetdb-daily-report.py
Script to print or email a daily Puppet run summary report using data from
a PuppetDB instance, accessed via nedap's pypuppetdb.

See README.rst for further information.

Requirements:
- pypuppetdb

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

import sys
import optparse
import logging
from . import VERSION
from pypuppetdb import connect

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.ERROR, format=FORMAT)
logger = logging.getLogger(__name__)

# these will probably be made configurable in the future
TOP_MODULES_COUNT = 10
TOP_RESOURCES_COUNT = 10


def main(hostname, dry_run=False):
    """
    main entry point

    :param hostname: PuppetDB hostname
    :type hostname: string
    :param dry_run: whether to actually send, or just print what would be sent
    :type dry_run: boolean
    """
    pdb = connect(host=hostname)

    # snapshot of PuppetDB metrics from the dashboard
    metrics = get_dashboard_metrics(pdb)

    # number of nodes with no successful runs, 50+% failed runs, any failed runs, less than 40 successful runs in 24 hours
    # top 10 failing resources, along with count of nodes they're failing on
    # top 10 modules causing failures

    # essentially figure out all these for yesterday, build the tables, serialize the result as JSON somewhere. then just keep the last ~7 days json files

    return True

def get_dashboard_metrics(pdb):
    """
    return a dict of the metrics displayed on the PuppetDB dashboard

    :param pdb: object representing a connected pypuppetdb instance
    :type pdb: one of the pypuppetdb.API classes
    """

    logger.debug("getting dashboard metrics...")

    metrics = {}
    metrics['JVM Heap'] = {'path': 'java.lang:type=Memory', value=None}

    """
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-nodes")
  .description("Nodes")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-resources")
  .description("Resources")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=pct-resource-dupes")
  .description("Resource duplication")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.scf.storage:type=default,name=duplicate-pct")
  .description("Catalog duplication")
  .url("/v2/metrics/mbean/org.apache.activemq:BrokerName=localhost,Type=Queue,Destination=com.puppetlabs.puppetdb.commands")
  .description("Command Queue")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command:type=global,name=processing-time")
  .description("Command Processing")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command:type=global,name=processed")
  .description("Command Processing")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command:type=global,name=processed")
  .description("Processed")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command:type=global,name=retried")
  .description("Retried")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command:type=global,name=discarded")
  .description("Discarded")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command:type=global,name=fatal")
  .description("Rejected")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.http.server:type=/v2/commands,name=service-time")
  .description("Enqueueing")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.http.server:type=/v2/resources,name=service-time")
  .description("Collection Queries")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.scf.storage:type=default,name=gc-time")
  .description("DB Compaction")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command.dlo:type=global,name=compression")
  .description("DLO Compression")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command.dlo:type=global,name=filesize")
  .description("DLO Size on Disk")
  .url("/v2/metrics/mbean/com.puppetlabs.puppetdb.command.dlo:type=global,name=messages")
  .description("Discarded Messages")
    """
    return metrics

def send_mail(body, dry_run=False):
    """
    Send the message

    :param body: body of the message to send
    :type body: string
    :param dry_run: whether to actually send, or just print what would be sent
    :type dry_run: boolean
    """
    if dry_run:
        logger.info("would have sent:")
    else:
        logger.debug("sending mail")
    return True


def parse_args(argv):
    """ parse arguments/options """
    p = optparse.OptionParser()

    p.add_option('-p', '--puppetdb', dest='host', action='store', type='string',
                 help='PuppetDB hostname')

    p.add_option('-n', '--num-days', dest='num_days', action='store', type='int', default=7,
                 help='Number of days to report on; default 7')

    p.add_option('-d', '--dry-run', dest='dry_run', action='store_true', default=False,
                 help='dry-run - dont actually send anything')

    p.add_option('-v', '--verbose', dest='verbose', action='count', default=0,
                 help='verbose output. specify twice for debug-level output.')

    options, args = p.parse_args(argv)

    return options


def console_entry_point():
    """setuptools entry point"""
    opts = parse_args(sys.argv[1:])

    if opts.verbose > 1:
        logger.setLevel(logging.DEBUG)
    elif opts.verbose > 0:
        logger.setLevel(logging.INFO)

    if opts:
        if not opts.host:
            raise SystemExit("ERROR: you must specify the PuppetDB hostname with -p|--puppetdb")
        main(opts.host, dry_run=opts.dry_run)


if __name__ == "__main__":
    console_entry_point()
