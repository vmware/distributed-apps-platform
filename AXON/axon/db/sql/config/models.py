#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from axon.db.sql.base import PickleEncodedList, BaseModel, passby

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String


Base = declarative_base(cls=BaseModel)


class ConnectedState(Base):
    __tablename__ = 'connectedstate'

    id = Column(String(36))
    endpoint = Column(String(36), primary_key=True)
    servers = Column(PickleEncodedList)
    clients = Column(PickleEncodedList)

    FIELDS = {
        'id': str,
        'endpoint': str,
        'servers': passby,
        'clients': passby
    }

    FIELDS.update(Base.FIELDS)
