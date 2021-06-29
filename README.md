[![Downloads](https://pepy.tech/badge/lydian)](https://pepy.tech/project/lydian)

# Distributed Apps Platform (LYDIAN)


**LYDIAN** is a general purpose *Distributed (Python) Apps Platform*. As the name suggests, it is based on Distributed Systems design principles and inherently supports  scalability and resiliency for the applications developed on the top of it. LYDIAN is written in native python and has a very minimal dependency on 3rd party modules. It's lightweight architecture helps it support hard to support platforms such as ESX. It's incredibly simple to use and is hgihly configurable.

Applications
------------

LYDIAN can be a good choice for developers for applications or tasks that need to be run in a large scale cluster environment. 

With LYDIAN, developers can focus on the actual task without having to worry about *Cluster management, RPC based communication channel, Cluster Scaling, Persistence and Resiliency* as all of that is taken care by `LYDIAN` platform.

Currently, following applications are supported on LYDIAN.

- Traffic Generation
- Vulnerability Scanning
- System and Health Monitoring.
- Packet Capture

Scale and Numbers
------------

LYDIAN has been tested with `Traffic Generation` at a `cluster of 5600+ nodes`, with a ping frequency of `~8 million pings per minute` leading to `1.2 Billion pings in less than 2 hours`.


Project Organization
------------

The project is organized as following. 

1. **LYDIAN** - Core engine of LYDIAN supporting distributed apps platform. 
2. **LYDIAN-UI** - A front end for cluster information. (In Progress)


Usage
------------

Usage details for LYDIAN command line can be found in [here](./LYDIAN/README.md) .
