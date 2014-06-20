"""
Test fixtures

Since we have objects (specifically datetime.timedelta) in here, we can't
really use JSON for this. The alternative is to pickle, but that makes it
a pain to work with.

"""
import datetime
from pypuppetdb.types import Event

FINAL_DATA = {
    'Tue 06/10': {
        'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
        'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
        'nodes': {
            'node1.example.com': {
                'reports': {
                    'run_count': 2,
                    'run_time_total': datetime.timedelta(seconds=1010),
                    'run_time_max': datetime.timedelta(seconds=1000),
                    'with_failures': 2,
                    'with_changes': 2,
                    'with_skips': 2,
                },
                'resources': {
                    'changed': {
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Service', u'winbind'): 1,
                        (u'Service', u'zookeeper-server'): 2,
                    },
                    'failed': {
                        (u'Package', u'libsmbios'): 1,
                        (u'Package', u'srvadmin-idrac7'): 2,
                    },
                    'skipped': {},
                },
            },
            'node2.example.com': {
                'reports': {
                    'run_count': 1,
                    'run_time_total': datetime.timedelta(seconds=100),
                    'run_time_max': datetime.timedelta(seconds=100),
                    'with_failures': 1,
                    'with_changes': 1,
                    'with_skips': 1,
                },
                'resources': {
                    'changed': {
                        (u'Service', u'zookeeper-server'): 2,
                    },
                    'failed': {},
                    'skipped': {
                        (u'Augeas', u'disable dell yum plugin once OM is installed'): 1,
                        (u'Service', u'dataeng'): 1,
                        (u'Exec', u'zookeeper ensemble check'): 1,
                    },
                },
            },
            'node3.example.com': {
                'reports': {
                    'run_count': 1,
                    'run_time_total': datetime.timedelta(seconds=500),
                    'run_time_max': datetime.timedelta(seconds=500),
                    'with_failures': 0,
                    'with_changes': 1,
                    'with_skips': 0,
                },
                'resources': {
                    'changed': {
                        (u'Service', u'winbind'): 1,
                    },
                    'failed': {
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Package', u'libsmbios'): 1,
                        (u'Package', u'srvadmin-idrac7'): 2,
                    },
                    'skipped': {
                        (u'Augeas', u'disable dell yum plugin once OM is installed'): 10,
                    },
                },
            },
            'node4.example.com': {
                'reports': {
                    'run_count': 5,
                    'run_time_total': datetime.timedelta(seconds=600),
                    'run_time_max': datetime.timedelta(seconds=500),
                    'with_failures': 5,
                    'with_changes': 0,
                    'with_skips': 0,
                },
                'resources': {}
            },
            'node5.example.com': {
                'reports': {
                    'run_count': 0,
                    'run_time_total': datetime.timedelta(),
                    'run_time_max': datetime.timedelta(),
                    'with_failures': 0,
                    'with_changes': 0,
                    'with_skips': 0,
                },
                'resources': {}
            },
            'node6.example.com': {
                'reports': {
                    'run_count': 10,
                    'run_time_total': datetime.timedelta(seconds=100),
                    'run_time_max': datetime.timedelta(seconds=90),
                    'with_failures': 7,
                    'with_changes': 2,
                    'with_skips': 7,
                },
                'resources': {}
            },
        },
        'aggregate': {
            'reports': {
                'run_count': 19,
                'run_time_avg': datetime.timedelta(0, 121, 578947),
                'run_time_max': datetime.timedelta(0, 1000),
                'run_time_total': datetime.timedelta(0, 2310),
                'with_changes': 6,
                'with_failures': 15,
                'with_skips': 10,
                'resources': {
                    'changed': {
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Service', u'winbind'): 2,
                        (u'Service', u'zookeeper-server'): 4,
                    },
                    'failed': {
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Package', u'libsmbios'): 2,
                        (u'Package', u'srvadmin-idrac7'): 4,
                    },
                    'skipped': {
                        (u'Augeas', u'disable dell yum plugin once OM is installed'): 11,
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Service', u'dataeng'): 1,
                    },
                },
            },
            'nodes': {
                'with_50+%_failed': 1,
                'with_changes': 4,
                'with_no_report': 1,
                'with_too_few_runs': 4,
                'with_skips': 3,
                'with_no_successful_runs': 4,
                'with_failures': 4,
                'resources': {
                    'changed': {
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Service', u'winbind'): 2,
                        (u'Service', u'zookeeper-server'): 2,
                    },
                    'failed': {
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Package', u'libsmbios'): 2,
                        (u'Package', u'srvadmin-idrac7'): 2,
                    },
                    'skipped': {
                        (u'Augeas', u'disable dell yum plugin once OM is installed'): 2,
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Service', u'dataeng'): 1,
                    },
                    'flapping': {
                        (u'Exec', u'zookeeper ensemble check'): 1,
                        (u'Service', u'winbind'): 2,
                        (u'Service', u'zookeeper-server'): 2,
                    },
                },
            },
        },
    },
    'Mon 06/09': {'metrics': {'foo': {'formatted': 'foo2'}, 'bar': {'formatted': 'bar2'}, 'baz': {'formatted': 'baz2'}}},
    'Sun 06/08': {'metrics': {'foo': {'formatted': 'foo3'}, 'bar': {'formatted': 'bar3'}, 'baz': {'formatted': 'baz3'}}},
    'Sat 06/07': {'metrics': {'foo': {'formatted': 'foo4'}, 'bar': {'formatted': 'bar4'}, 'baz': {'formatted': 'baz4'}}},
    'Fri 06/06': {'metrics': {'foo': {'formatted': 'foo5'}, 'bar': {'formatted': 'bar5'}, 'baz': {'formatted': 'baz5'}}},
    'Thu 06/05': {'metrics': {'foo': {'formatted': 'foo6'}, 'bar': {'formatted': 'bar6'}, 'baz': {'formatted': 'baz6'}}},
    'Wed 06/04': {'foo': 'bar'},
}

FINAL_DATES = ['Tue 06/10',
               'Mon 06/09',
               'Sun 06/08',
               'Sat 06/07',
               'Fri 06/06',
               'Thu 06/05',
               'Wed 06/04'
               ]

NODE_SUMMARY_DATA = {
    'Tue 06/10': {
        'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
        'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
        'nodes': {
            'node1.example.com': {
                'reports': {
                    'run_count': 2,
                    'run_time_total': datetime.timedelta(seconds=1010),
                    'run_time_max': datetime.timedelta(seconds=1000),
                    'with_failures': 2,
                    'with_changes': 2,
                    'with_skips': 2,
                },
            },
        },
        'aggregate': {
            'reports': {
                'with_skips': 3,
                'run_time_max': datetime.timedelta(0, 1000),
                'with_failures': 8,
                'with_changes': 4,
                'run_count': 9,
                'run_time_total': datetime.timedelta(0, 2210),
                'run_time_avg': datetime.timedelta(0, 245, 555555),
                'nodes_with_no_report': 1,
            },
            'nodes': {
                'count': 10,
                'all_failed': 1,
                'half_failed': 4,
                'any_failed': 2,
                'less_than_X_reports': 1,
                'with_changes': 5,
            },
        },
    },
    'Mon 06/09': {
        'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
        'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
        'nodes': {
            'node1.example.com': {
                'reports': {
                    'run_count': 2,
                    'run_time_total': datetime.timedelta(seconds=1010),
                    'run_time_max': datetime.timedelta(seconds=1000),
                    'with_failures': 2,
                    'with_changes': 2,
                    'with_skips': 2,
                },
            },
        },
        'aggregate': {
            'reports': {
                'with_skips': 3,
                'run_time_max': datetime.timedelta(0, 1000),
                'with_failures': 8,
                'with_changes': 4,
                'run_count': 9,
                'run_time_total': datetime.timedelta(0, 2210),
                'run_time_avg': datetime.timedelta(0, 245, 555555),
                'nodes_with_no_report': 1,
            },
            'nodes': {
                'count': 8,
                'all_failed': 4,
                'half_failed': 0,
                'any_failed': 2,
                'less_than_X_reports': 0,
                'with_changes': 6,
            },
        },
    },
    'Sun 06/08': {'metrics': {'foo': {'formatted': 'foo3'}, 'bar': {'formatted': 'bar3'}, 'baz': {'formatted': 'baz3'}}},
    'Sat 06/07': {'metrics': {'foo': {'formatted': 'foo4'}, 'bar': {'formatted': 'bar4'}, 'baz': {'formatted': 'baz4'}}},
    'Fri 06/06': {'metrics': {'foo': {'formatted': 'foo5'}, 'bar': {'formatted': 'bar5'}, 'baz': {'formatted': 'baz5'}}},
    'Thu 06/05': {'metrics': {'foo': {'formatted': 'foo6'}, 'bar': {'formatted': 'bar6'}, 'baz': {'formatted': 'baz6'}}},
    'Wed 06/04': {'foo': 'bar'},
}

NODE_AGGR_NODES = {
    'node1.example.com': {
        'reports': {
            'run_count': 1,
            'run_time_total': datetime.timedelta(seconds=100),
            'run_time_max': datetime.timedelta(seconds=100),
            'with_failures': 1,
            'with_changes': 1,
            'with_skips': 1,
        },
    },
    'node2.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node3.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node4.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node5.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node6.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node7.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node8.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node9.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
    'node10.example.com': {
        'reports': {
            'run_count': 2,
            'run_time_total': datetime.timedelta(seconds=1010),
            'run_time_max': datetime.timedelta(seconds=1000),
            'with_failures': 2,
            'with_changes': 2,
            'with_skips': 2,
        },
    },
}

EVENT_DATA = {
    '["=", "report", "hash1"]': [
        Event(
            u'node1.example.com',
            u'otherstatus',
            u'2014-06-18T13:02:54.122000Z',
            u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            u'srvadmin-idrac7',
            u'ensure',
            u'failure message here',
            u'present',
            u'absent',
            u'Package',
        ),
    ],
    '["=", "report", "hash2"]': [
        Event(
            u'node1.example.com',
            u'failure',
            u'2014-06-18T13:02:54.122000Z',
            u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            u'srvadmin-idrac7',
            u'ensure',
            u'failure message here',
            u'present',
            u'absent',
            u'Package',
        ),
        Event(
            u'node1.example.com',
            u'skipped',
            u'2014-06-18T13:03:03.099000Z',
            u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            u'dataeng',
            None,
            None,
            None,
            None,
            u'Service',
        ),
        Event(
            u'node1.example.com',
            u'failure',
            u'2014-06-18T13:03:02.995000Z',
            u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            u'libsmbios',
            u'ensure',
            u'failure message here',
            u'latest',
            u'2.2.26-3.el5',
            u'Package',
        ),
        Event(
            u'node1.example.com',
            u'skipped',
            u'2014-06-18T13:03:03.100000Z',
            u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            u'disable dell yum plugin once OM is installed',
            None,
            None,
            None,
            None,
            u'Augeas',
        ),
    ],
    '["=", "report", "hash3"]': [
        Event(
            u'node1.example.com',
            u'success',
            u'2014-06-18T13:00:55.300000Z',
            u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            u'zookeeper ensemble check',
            u'returns',
            u'executed successfully',
            [u'0'],
            u'notrun',
            u'Exec',
        ),
        Event(
            u'node1.example.com',
            u'success',
            u'2014-06-18T13:01:00.122000Z',
            u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            u'winbind',
            u'ensure',
            u"ensure changed 'stopped' to 'running'",
            u'running',
            u'stopped',
            u'Service',
        ),
        Event(
            u'node1.example.com',
            u'success',
            u'2014-06-18T13:00:54.129000Z',
            u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            u'zookeeper-server',
            u'ensure',
            u"ensure changed 'stopped' to 'running'",
            u'running',
            u'stopped',
            u'Service',
        ),
    ],
    '["=", "report", "hash4"]': [
        Event(
            u'node1.example.com',
            u'failure',
            u'2014-06-18T13:02:54.122000Z',
            u'14eaf89f52496f94bae336d454b60fac6189ff1b',
            u'srvadmin-idrac7',
            u'ensure',
            u'failure message here',
            u'present',
            u'absent',
            u'Package',
        ),
        Event(
            u'node1.example.com',
            u'success',
            u'2014-06-18T13:00:54.129000Z',
            u'c5a40c3068f295966541d7e51d3e6fe76e56870c',
            u'zookeeper-server',
            u'ensure',
            u"ensure changed 'stopped' to 'running'",
            u'running',
            u'stopped',
            u'Service',
        ),
    ],
}

FLAPPING_DATA = {
    'metrics': {'foo': {'formatted': 'foo1'}, 'bar': {'formatted': 'bar1'}, 'baz': {'formatted': 'baz1'}},
    'facts': {'puppetversion': {'3.4.1': 2, '3.4.2': 1, '3.6.1': 100}, 'facterversion': {'2.0.0': 102, '1.7.2': 1}},
    'nodes': {
        'node1.example.com': {
            'reports': {
                'run_count': 10,
                'run_time_total': datetime.timedelta(seconds=1010),
                'run_time_max': datetime.timedelta(seconds=1000),
                'with_failures': 2,
                'with_changes': 2,
                'with_skips': 2,
            },
            'resources': {
                'changed': {
                    (u'Exec', u'zookeeper ensemble check'): 10,
                    (u'Package', u'libsmbios'): 5,
                    (u'Package', u'srvadmin-idrac7'): 4,
                    (u'Service', u'dataeng'): 10,
                },
                'failed': {},
                'skipped': {},
            },
        },
        'node2.example.com': {
            'reports': {
                'run_count': 10,
                'run_time_total': datetime.timedelta(seconds=100),
                'run_time_max': datetime.timedelta(seconds=100),
                'with_failures': 1,
                'with_changes': 1,
                'with_skips': 1,
            },
            'resources': {
                'changed': {
                    (u'Exec', u'zookeeper ensemble check'): 10,
                    (u'Package', u'libsmbios'): 9,
                    (u'Package', u'srvadmin-idrac7'): 4,
                    (u'Service', u'dataeng'): 10,
                    (u'Service', u'winbind'): 5,
                },
                'failed': {},
                'skipped': {},
            },
        },
        'node3.example.com': {
            'reports': {
                'run_count': 10,
                'run_time_total': datetime.timedelta(seconds=500),
                'run_time_max': datetime.timedelta(seconds=500),
                'with_failures': 0,
                'with_changes': 1,
                'with_skips': 0,
            },
            'resources': {
                'changed': {
                    (u'Exec', u'zookeeper ensemble check'): 10,
                    (u'Package', u'libsmbios'): 11,
                    (u'Package', u'srvadmin-idrac7'): 1,
                    (u'Service', u'dataeng'): 5,
                    (u'Service', u'winbind'): 6,
                    (u'Service', u'zookeeper-server'): 9,
                },
                'failed': {},
                'skipped': {},
            },
        },
        'node4.example.com': {
            'reports': {
                'run_count': 10,
                'run_time_total': datetime.timedelta(seconds=600),
                'run_time_max': datetime.timedelta(seconds=500),
                'with_failures': 5,
                'with_changes': 0,
                'with_skips': 0,
            },
            'resources': {
                'changed': {
                    (u'Exec', u'zookeeper ensemble check'): 10,
                    (u'Package', u'libsmbios'): 1,
                    (u'Package', u'srvadmin-idrac7'): 4,
                    (u'Service', u'winbind'): 4,
                },
                'failed': {},
                'skipped': {},
            },
        },
        'node5.example.com': {
            'reports': {
                'run_count': 10,
                'run_time_total': datetime.timedelta(),
                'run_time_max': datetime.timedelta(),
                'with_failures': 0,
                'with_changes': 0,
                'with_skips': 0,
            },
            'resources': {
                'changed': {
                    (u'Exec', u'zookeeper ensemble check'): 5,
                    (u'Package', u'libsmbios'): 3,
                    (u'Package', u'srvadmin-idrac7'): 3,
                    (u'Service', u'winbind'): 4,
                    (u'Service', u'zookeeper-server'): 7,
                },
                'failed': {},
                'skipped': {},
            },
        },
        'node6.example.com': {
            'reports': {
                'run_count': 10,
                'run_time_total': datetime.timedelta(seconds=100),
                'run_time_max': datetime.timedelta(seconds=90),
                'with_failures': 7,
                'with_changes': 2,
                'with_skips': 7,
            },
            'resources': {
                'changed': {
                    (u'Augeas', u'disable dell yum plugin once OM is installed'): 10,
                    (u'Exec', u'zookeeper ensemble check'): 8,
                    (u'Package', u'libsmbios'): 4,
                    (u'Package', u'srvadmin-idrac7'): 2,
                    (u'Service', u'winbind'): 1,
                    (u'Service', u'zookeeper-server'): 6,
                },
                'failed': {},
                'skipped': {},
            },
        },
    },
}
