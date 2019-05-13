# Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - API v2



class FIMAuthExcetpion(Exception):
    def __init__(self, message):
        super(FIMAuthExcetpion, self).__init__(message)


class FIMAResouceExistingException(Exception):
    def __init__(self, message):
        super(FIMAResouceExistingException, self).__init__(message)


class FIMNotFoundException(Exception):
    def __init__(self, message):
        super(FIMNotFoundException, self).__init__(message)


class FIMTaskFailedException(Exception):
    def __init__(self, message):
        super(FIMTaskFailedException, self).__init__(message)
