#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Gamma-Scientific light-measuring devices.

Tested with S470, but should work with S480 and S490, too.

These are optional components that can be obtained by installing the
`psychopy-gammasci` extension into the current environment.

"""

from psychopy.plugins import PluginStub


class S470(
    PluginStub, 
    plugin="psychopy-gammasci", 
    docsHome="https://psychopy.github.io/psychopy-gammasci",
    docsRef="/coder/S470"
):
    pass
