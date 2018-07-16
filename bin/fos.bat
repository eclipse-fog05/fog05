REM # Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
REM # 
REM # See the NOTICE file(s) distributed with this work for additional
REM # information regarding copyright ownership.
REM # 
REM # This program and the accompanying materials are made available under the
REM # terms of the Eclipse Public License 2.0 which is available at
REM # http://www.eclipse.org/legal/epl-2.0
REM # 
REM # SPDX-License-Identifier: EPL-2.0
REM #
REM # Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Initial implementation and API



@echo off
set PYFILE=%~f0
set PYFILE=%PYFILE:~0,-3%
"python.exe" "%PYFILE%" %*