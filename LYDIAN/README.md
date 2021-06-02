
# LYDIAN

LYDIAN is a distributed (python) apps platform. It has apps for Traffic Generation, Resource Monitoring, Vulnerability Scan.

It is based on Distributed System principles. It uses RPC for communication across nodes, Local Database for persistence and Daemon services for resiliency.

LYDIAN has its own in-built simple TCP/UDP client and servers for Traffic Generation and it also offers simple integration with other 3rd party tools such as IPERF. It recognizes the collection of nodes (to and from where traffic needs to be generated) as a "Cluster" and nodes can be attached and detached to cluster at any time during the operation.

Installation
------------

LYDIAN is available as Python package and can be installed on Primary nodes using `pip` as following.

```
pip install lydian
```


Usage
------------

LYDIAN is simple to use. Below are some examples for different capabilities which are available.

####  Running Traffic

```python
import time
import uuid

from lydian.apps.podium import get_podium

PASSWD = 'MY_PASSWORD'  # Password for SSH access to nodes.
VM0_IP = 'a.b.c.d'
VM1_IP = 'w.x.y.z'

podium = get_podium()
podium.add_hosts(VM0_IP, password=PASSWD)
podium.add_hosts(VM1_IP, password=PASSWD)
# podium.add_endpoints(vms[0].ip, password=PASSWD)
# podium.add_endpoints(vms[1].ip, password=PASSWD)


DUMMY_RULE = {
    'reqid': '%s' % uuid.uuid4(),
    'ruleid': '%s' % uuid.uuid4(),
    'src': VM0_IP,
    'dst': VM1_IP,
    'protocol': 'TCP',
    'port': 9465,
    'connected': True
    }
rules = []
# Create Rule 1
rules.append(DUMMY_RULE)

# Ask the tool to register your intent.
podium.register_traffic(rules)

```

####  Packet Capture

```python
from lydian.apps.podium import get_podium
from lydian.utils.ssh_host import Host

VM_IP = '1.2.3.4'

# Delete any old PCAP file at endpoint
with Host(VM_IP, user='root', passwd='PASSWD') as host:
    host.req_call('rm -rf /tmp/test_pcap.pcap')

# Also remove any local file
try:
    os.remove('/tmp/test_pcap.pcap')
except FileNotFoundError:
    pass

podium = get_podium()

# Prepare the node (if not done already)
podium.add_hosts(VM_IP, password=PASSWD)

# Start Packet Capture
podium.start_pcap(VM_IP, pcap_file_name='test_pcap.pcap', interface='eth0')
time.sleep(10)
podium.stop_pcap(vm1, pcap_file_name='test_pcap.pcap')

# Download file locally.
with Host(VM_IP, user='root', passwd='PASSWD') as host:
    host.get_file('rm -rf /tmp/test_pcap.pcap')

# Run any tool on this file like tcpreplay/ wireshark on this file or simply check
# that file exists.
assert os.path.exists(os.path.join('/tmp', 'test_pcap.pcap'))

```
####  Generating Traffic from IPERF

```python
from lydian.apps.podium import get_podium

podium = get_podium()
# Prepare the nodes (if not done already)
podium.add_hosts(VM1_IP, password=PASSWD)
podium.add_hosts(VM2_IP, password=PASSWD)

result = podium.run_iperf3(src_ip, dst_ip)
result_dict = json.loads(result)
```

Repository & License
------------
LYDIAN is an Open Source Software (OSS) hosted at https://github.com/vmware/distributed-apps-platform. Check LICENSE.txt for applicable licenses.

https://github.com/vmware/distributed-apps-platform

Requirements
------------
Python 3.6.8+

Share and enjoy!
