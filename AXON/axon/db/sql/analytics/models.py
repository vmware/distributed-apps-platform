#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from axon.db.sql.base import BaseModel

from sqlalchemy import Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, Float, Integer


Base = declarative_base(cls=BaseModel)


class TrafficRecord(Base):
    __tablename__ = 'trafficrecord'
    __table_args__ = (
        Index('created_idx', 'created'),
        Index('success_idx', 'success'),
        Index('src_idx', 'src'), Index('dst_idx', 'dst'))

    id = Column(String(36), primary_key=True)
    src = Column(String(36))
    dst = Column(String(36))
    port = Column(Integer())
    latency = Column(Float())
    success = Column(Boolean(), default=True)
    type = Column(String(10))
    created = Column(Float())
    connected = Column(Boolean())

    FIELDS = {
        'src': str,
        'dst': str,
        'port': int,
        'latency': float,
        'type': str,
        'created': int,
    }

    FIELDS.update(Base.FIELDS)


class LatencyStats(Base):
    __tablename__ = 'latencystats'

    id = Column(String(36), primary_key=True)
    created = Column(Float())
    latency_sum = Column(Integer())
    samples = Column(Integer())


class RequestCount(Base):
    __tablename__ = 'requestcount'
    id = Column(String(36), primary_key=True)
    created = Column(Float())
    success = Column(Integer())
    failure = Column(Integer())
    type = Column(String(10))

    FIELDS = {
        'created': float,
        'success': int,
        'failure': int,
        'type': str
    }

    FIELDS.update(Base.FIELDS)


class Fault(Base):

    __tablename__ = 'fault'

    id = Column(String(36), primary_key=True)
    src = Column(String(36))
    dst = Column(String(36))
    port = Column(Integer())
    error = Column(String(100))
    type = Column(String(10))
    created = Column(Float())
    connected = Column(Boolean())

    FIELDS = {
        'src': str,
        'dst': str,
        'port': int,
        'error': str,
        'type': str,
        'created': int,
        'connected': bool

    }

    FIELDS.update(Base.FIELDS)


class ResourceMetrics(Base):
    __tablename__ = 'resourcemetrics'
    id = Column(String(36), primary_key=True)
    created = Column(Float())
    syscpu = Column(Float())
    sysmem = Column(Float())
    axoncpu = Column(Float())
    axonmem = Column(Float())
    type = Column(String(10))

    FIELDS = {
        'created': float,
        'syscpu': float,
        'sysmem': float,
        'axoncpu': float,
        'axonmem': float,
    }

    FIELDS.update(Base.FIELDS)
