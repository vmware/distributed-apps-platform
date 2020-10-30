#!/usr/bin/env python
'''
A simple test using LYDIAN.

USAGE:
    sudo python -mlydian.tests.integration.test_demo \
        -u root -p my_password -e ip1 ip2
'''
import argparse
import logging
import time
import uuid

from lydian.apps.podium import get_podium, start_pcap, \
    stop_pcap, start_resource_monitoring, \
    stop_resource_monitoring, run_iperf3
from lydian.utils.prep import prep_node, cleanup_node
from lydian.utils.ssh_host import Host
import lydian.utils.logger as logger

log = logging.getLogger(__name__)

VM0_IP = 'a.b.c.d'
VM1_IP = 'w.x.y.z'
USERNAME = 'root'
PASSWD = 'FAKE_PASSWORD'


def run_demo(testbed):
    DUMMY_RULE = {
        'reqid': '%s' % uuid.uuid4(),
        'ruleid': '%s' % uuid.uuid4(),
        'src': VM0_IP,
        'dst': VM1_IP,
        'protocol': 'TCP',
        'tries': 10,
        'payload': 'NDBU',
        'port': 9465,
        'connected': True
    }

    tb = testbed
    vms = tb.vms
    vm0, vm1 = vms[0], vms[1]
    podium = get_podium()
    podium.add_hosts(vms[0].ip, password=PASSWD)
    podium.add_hosts(vms[1].ip, password=PASSWD)

    rules = []
    # Create Rule 1
    rules.append(DUMMY_RULE)

    # Create Rule 2
    rule = dict(DUMMY_RULE)
    rule['src'], rule['dst'] = rule['dst'], rule['src']
    rule['reqid'] = '%s' % uuid.uuid4()
    rule['ruleid'] = '%s' % uuid.uuid4()
    rules.append(rule)

    # Create Rule 3
    rule = dict(DUMMY_RULE)
    rule['ruleid'] = '%s' % uuid.uuid4()
    rules.append(rule)

    podium.register_traffic(rules)

    # Start Packet Capture
    start_pcap(vm0, 'one.pcap', 'eth0')

    # Stop resource monitoring on a node.
    stop_resource_monitoring(vm1)

    # Stop Packet Capture
    stop_pcap(vm0, 'one.pcap')

    # Stop resource monitoring on a node.
    start_resource_monitoring(vm1)

    result = run_iperf3(vm1.ip, vm0.ip)
    log.info("IPERF Results : %s", result)

    time.sleep(200)
    cleanup_node(vms[0].ip, username=USERNAME, password=PASSWD)
    cleanup_node(vms[1].ip, username=USERNAME, password=PASSWD)


def process_nodes(vms):
    """
    Process Nodes
    """
    for vm in vms:
        with Host(vm.ip, user=USERNAME, passwd=PASSWD) as host:
            try:
                host.req_call('hostname %s' % vm.name)
                host.req_call('route add default gw 10.149.55.253 eth0')
                host.req_call('cp /etc/network/interfaces.d/eth0 '
                              '/etc/network/interfaces.d/eth1')
                host.req_call("sed -i 's/eth0/eth1/g' "
                              "/etc/network/interfaces.d/eth1")
                host.req_call("ifdown eth1 ; ifup eth1")
            except Exception as err:
                _ = err


def main():
    class Testbed(object):
        pass

    class VM(object):
        pass

    tb = Testbed()
    vms = [VM(), VM()]
    vms[0].ip = VM0_IP
    vms[1].ip = VM1_IP
    vms[0].name = 'vm0'
    vms[1].name = 'vm1'
    tb.vms = vms

    cleanup_node(vms[0].ip, username=USERNAME, password=PASSWD)
    cleanup_node(vms[1].ip, username=USERNAME, password=PASSWD)
    run_demo(tb)


if __name__ == '__main__':
    desc = 'LYDIAN Demo'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-u', '--username',
                        help='username to access hosts.')

    parser.add_argument('-p', '--password',
                        help='Passowrd for hosts.')

    parser.add_argument('-e', '--endpoints', nargs='+', required=True,
                        help='optimize for site span')

    args = parser.parse_args()

    if args.username:
        USERNAME = args.username

    if args.password:
        PASSWD = args.password

    if not args.endpoints:
        print("Not Hosts Porovided.")
    else:
        VM0_IP, VM1_IP = args.endpoints[0], args.endpoints[1]
        logger.setup_logging()
        main()
