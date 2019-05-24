# Copyright (c) 2014,2019 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
#
# Contributors: Luca Cominardi, University Carlos III of Madrid.

import datetime
import logging


def _fmt_time(log_cls, record, dateftm = None):
    return datetime.datetime.now().strftime('%H:%M:%S.%f')


def Logger(name, uuid):
    # Define and set logging time format
    logging.Formatter.formatTime = _fmt_time

    # Set logging colors
    logging.addLevelName(logging.DEBUG,
            "\033[1;34m{}\033[1;0m".format(logging.getLevelName(logging.DEBUG)))
    logging.addLevelName(logging.INFO,
            "\033[1;32m{}\033[1;0m".format(logging.getLevelName(logging.INFO)))
    logging.addLevelName(logging.WARNING,
            "\033[1;33m{}\033[1;0m".format(logging.getLevelName(logging.WARNING)))
    logging.addLevelName(logging.ERROR,
            "\033[1;31m{}\033[1;0m".format(logging.getLevelName(logging.ERROR)))
    logging.addLevelName(logging.CRITICAL,
            "\033[1;41m{}\033[1;0m".format(logging.getLevelName(logging.CRITICAL)))

    # Create the logger
    l = logging.getLogger(uuid)
    # Set level to Debug by default
    l.setLevel(logging.DEBUG)

    # Create a console handler
    ch = logging.StreamHandler()
    fmt = logging.Formatter('\033[32m%(asctime)s\033[0m [%(levelname)s][\033[93m{}\033[0m][\033[95m{}\033[0m] %(message)s'.format(name, uuid))
    ch.setFormatter(fmt)
    l.addHandler(ch)

    return l
