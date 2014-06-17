"""
Test fixtures

Since we have objects (specifically datetime.timedelta) in here, we can't
really use JSON for this. The alternative is to pickle, but that makes it
a pain to work with.

"""
import datetime

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
        'nodes': { 'node1.example.com': {
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
        'nodes': { 'node1.example.com': {
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
    # TODO - left off here
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
