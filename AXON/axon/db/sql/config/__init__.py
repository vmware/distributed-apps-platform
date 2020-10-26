#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from contextlib import contextmanager
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


def get_engine(uri):
    return create_engine(uri)


if os.name == "posix":
   VALIDATION_CONFIG_DB_URL = "sqlite:////opt/axon/config.db"
else:
   VALIDATION_CONFIG_DB_URL = "sqlite:///C:\\axon\\config.db"

VALIDATION_CONFIG_DB_URL = os.getenv('VALIDATION_CONFIG_DB_URL',
                                     VALIDATION_CONFIG_DB_URL)

cs_db_session = scoped_session(sessionmaker(
    autoflush=True,
    autocommit=False))
cs_engine = get_engine(VALIDATION_CONFIG_DB_URL)


def init_session():
    cs_db_session.configure(bind=cs_engine)
    from axon.db.sql.config.models import Base
    Base.metadata.create_all(cs_engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = cs_db_session
    # reconfiguring bind engine in db session to avoid windows threading issue
    session.configure(bind=cs_engine)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
