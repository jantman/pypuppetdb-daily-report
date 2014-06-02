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
import requests

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
    metrics['JVM Heap'] = {'path': 'java.lang:type=Memory', 'order': 1, 'value': None}
    metrics['Nodes'] = {'path': 'com.puppetlabs.puppetdb.query.population:type=default,name=num-nodes', 'order': 2, 'value': None}
    metrics['Resources'] = {'path': 'com.puppetlabs.puppetdb.query.population:type=default,name=num-resources', 'order': 3, 'value': None}
    metrics['Resource Duplication'] = {'path': 'com.puppetlabs.puppetdb.query.population:type=default,name=pct-resource-dupes', 'order': 4, 'value': None}
    metrics['Catalog duplication'] = {'path': 'com.puppetlabs.puppetdb.scf.storage:type=default,name=duplicate-pct', 'order': 5, 'value': None}
    metrics['Command Queue'] = {'path': 'org.apache.activemq:BrokerName=localhost,Type=Queue,Destination=com.puppetlabs.puppetdb.commands', 'order': 6, 'value': None}
    metrics['Command Processing Time'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=processing-time', 'order': 7, 'value': None}
    metrics['Command Processing'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=processed', 'order': 8, 'value': None}
    metrics['Processed'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=processed', 'order': 9, 'value': None}
    metrics['Retired'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=retried', 'order': 10, 'value': None}
    metrics['Discarded'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=discarded', 'order': 11, 'value': None}
    metrics['Rejected'] = {'path': 'com.puppetlabs.puppetdb.command:type=global,name=fatal', 'order': 12, 'value': None}
    metrics['Enqueueing'] = {'path': 'com.puppetlabs.puppetdb.http.server:type=/v2/commands,name=service-time', 'order': 13, 'value': None}
    metrics['Collection Queries'] = {'path': 'com.puppetlabs.puppetdb.http.server:type=/v2/resources,name=service-time', 'order': 14, 'value': None}
    metrics['DB Compaction'] = {'path': 'com.puppetlabs.puppetdb.scf.storage:type=default,name=gc-time', 'order': 15, 'value': None}
    metrics['DLO Compression'] = {'path': 'com.puppetlabs.puppetdb.command.dlo:type=global,name=compression', 'order': 16, 'value': None}
    metrics['DLO Size on Disk'] = {'path': 'com.puppetlabs.puppetdb.command.dlo:type=global,name=filesize', 'order': 17, 'value': None}
    metrics['Discarded Messages'] = {'path': 'com.puppetlabs.puppetdb.command.dlo:type=global,name=messages', 'order': 18, 'value': None}

    for metric in metrics:
        logger.debug("getting metric: %s" % metric)
        try:
            metrics[metric]['value'] = pdb.metric(metrics[metric]['path'])
            logger.debug("got raw value: %s" % metrics[metric]['value'])
            metrics[metric]['value'] = metric_value(metrics[metric]['value'])
            logger.debug("setting value to: %s" % metrics[metric]['value'])
        except requests.exceptions.HTTPError:
            logger.debug("unable to get value for metric: %s" % metric)
    logger.info("got dashboard metrics")
    return metrics


def metric_value(m):
    """
    Takes a dict returned by the metric() API endpoint, returns the formatted value we want to track.
    """
    if 'Value' in m:
        return "{:,f}".format(m['Value'])
    if 'MeanRate' in m and 'Count' in m:
        return "{:,f} ({:d})".format(m['MeanRate'], m['Count'])
    if 'MeanRate' in m:
        return "{:,f}".format(m['MeanRate'])
    return m


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
