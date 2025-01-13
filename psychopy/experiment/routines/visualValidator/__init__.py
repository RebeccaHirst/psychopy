#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.alerts._alerts import alert
from psychopy.experiment import Param
from psychopy.experiment.plugins import PluginDevicesMixin, DeviceBackend
from psychopy.experiment.components import getInitVals
from psychopy.experiment.routines import Routine, BaseValidatorRoutine
from psychopy.localization import _translate


class VisualValidatorRoutine(BaseValidatorRoutine, PluginDevicesMixin):
    """
    Use a light sensor to confirm that visual stimuli are presented when they should be.
    """
    targets = ['PsychoPy']

    categories = ['Validation']
    iconFile = Path(__file__).parent / 'photodiode_validator.png'
    tooltip = _translate(
        "Use a light sensor to confirm that visual stimuli are presented when they should be."
    )
    deviceClasses = []
    version = "2025.1.0"

    def __init__(
            self,
            # basic
            exp, name='visualVal',
            findThreshold=True, threshold=127,
            # layout
            findDiode=True, diodePos="(1, 1)", diodeSize="(0.1, 0.1)", diodeUnits="norm",
            # device
            deviceLabel="", deviceBackend="screenbuffer", port="", channel="0",
    ):

        self.exp = exp  # so we can access the experiment if necess
        self.params = {}
        self.depends = []
        super(VisualValidatorRoutine, self).__init__(exp, name=name)
        self.order += []
        self.type = 'PhotodiodeValidator'

        exp.requireImport(
            importName="photodiode",
            importFrom="psychopy.hardware",
            importAs="phd"
        )

        # --- Basic ---
        self.order += [
            "findThreshold",
            "threshold",
            "findDiode",
            "diodePos",
            "diodeSize",
            "diodeUnits",
        ]
        self.params['findThreshold'] = Param(
            findThreshold, valType="bool", inputType="bool", categ="Basic",
            label=_translate("Find best threshold?"),
            hint=_translate(
                "Run a brief Routine to find the best threshold for the light sensor at experiment start?"
            )
        )
        self.params['threshold'] = Param(
            threshold, valType="code", inputType="single", categ="Basic",
            label=_translate("Threshold"),
            hint=_translate(
                "Light threshold at which the light sensor should register a positive, units go from 0 (least light) to "
                "255 (most light)."
            )
        )
        self.depends.append({
            "dependsOn": "findThreshold",  # if...
            "condition": "==True",  # is...
            "param": "threshold",  # then...
            "true": "hide",  # should...
            "false": "show",  # otherwise...
        })
        self.params['findDiode'] = Param(
            findDiode, valType="code", inputType="bool", categ="Basic",
            label=_translate("Find diode?"),
            hint=_translate(
                "Run a brief Routine to find the size and position of the light sensor at experiment start?"
            )
        )
        self.params['diodePos'] = Param(
            diodePos, valType="list", inputType="single", categ="Basic",
            updates="constant", allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            label=_translate("Position [x,y]"),
            hint=_translate(
                "Position of the light sensor on the window."
            )
        )
        self.params['diodeSize'] = Param(
            diodeSize, valType="list", inputType="single", categ="Basic",
            updates="constant", allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            label=_translate("Size [x,y]"),
            hint=_translate(
                "Size of the area covered by the light sensor on the window."
            )
        )
        self.params['diodeUnits'] = Param(
            diodeUnits, valType="str", inputType="choice", categ="Basic",
            allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm', 'height', 'degFlatPos', 'degFlat'],
            label=_translate("Spatial units"),
            hint=_translate(
                "Spatial units in which the light sensor size and position are specified."
            )
        )
        for param in ("diodePos", "diodeSize", "diodeUnits"):
            self.depends.append({
                "dependsOn": "findDiode",  # if...
                "condition": "==True",  # is...
                "param": param,  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            })

        del self.params['stopType']
        del self.params['stopVal']

        # --- Device ---
        self.order += [
            "deviceLabel",
            "deviceBackend",
            "channel",
        ]
        self.params['deviceLabel'] = Param(
            deviceLabel, valType="str", inputType="single", categ="Device",
            label=_translate("Device name"),
            hint=_translate(
                "A name to refer to this Component's associated hardware device by. If using the "
                "same device for multiple components, be sure to use the same name here."
            )
        )
        self.params['deviceBackend'] = Param(
            deviceBackend, valType="code", inputType="choice", categ="Device",
            allowedVals=self.getBackendKeys,
            allowedLabels=self.getBackendLabels,
            label=_translate("Light sensor type"),
            hint=_translate(
                "Type of light sensor to use."
            ),
            direct=False
        )
        self.params['channel'] = Param(
            channel, valType="code", inputType="single", categ="Device",
            label=_translate("Light sensor channel"),
            hint=_translate(
                "If relevant, a channel number attached to the light sensor, to distinguish it "
                "from other light sensors on the same port. Leave blank to use the first light sensor "
                "which can detect the Window."
            )
        )

        self.loadBackends()

    def writeDeviceCode(self, buff):
        """
        Code to setup the CameraDevice for this component.

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        """
        # do usual backend-specific device code writing
        PluginDevicesMixin.writeDeviceCode(self, buff)
        # get inits
        inits = getInitVals(self.params)
        # get device handle
        code = (
            "%(deviceLabelCode)s = deviceManager.getDevice(%(deviceLabel)s)"
        )
        buff.writeOnceIndentedLines(code % inits)
        # find threshold if indicated
        if self.params['findThreshold']:
            code = (
                "# find threshold for light sensor\n"
                "if %(deviceLabelCode)s.getThreshold(channel=%(channel)s) is None:\n"
                "    %(deviceLabelCode)s.findThreshold(win, channel=%(channel)s)\n"
            )
        else:
            code = (
                "%(deviceLabelCode)s.setThreshold(%(threshold)s, channel=%(channel)s)"
            )
        buff.writeOnceIndentedLines(code % inits)
        # find pos if indicated
        if self.params['findDiode']:
            code = (
                "# find position and size of light sensor\n"
                "if %(deviceLabelCode)s.pos is None and %(deviceLabelCode)s.size is None and %(deviceLabelCode)s.units is None:\n"
                "    %(deviceLabelCode)s.findPhotodiode(win, channel=%(channel)s)\n"
            )
            buff.writeOnceIndentedLines(code % inits)

    def writeMainCode(self, buff):
        inits = getInitVals(self.params)
        # get diode
        code = (
            "# diode object for %(name)s\n"
            "%(name)sDiode = deviceManager.getDevice(%(deviceLabel)s)\n"
        )
        buff.writeIndentedLines(code % inits)

        if self.params['threshold'] and not self.params['findThreshold']:
            code = (
                "%(name)sDiode.setThreshold(%(threshold)s, channel=%(channel)s)\n"
            )
            buff.writeIndentedLines(code % inits)
        # find/set diode position
        if not self.params['findDiode']:
            code = ""
            # set units (unless None)
            if self.params['diodeUnits']:
                code += (
                    "%(name)sDiode.units = %(diodeUnits)s\n"
                )
            # set pos (unless None)
            if self.params['diodePos']:
                code += (
                    "%(name)sDiode.pos = %(diodePos)s\n"
                )
            # set size (unless None)
            if self.params['diodeSize']:
                code += (
                    "%(name)sDiode.size = %(diodeSize)s\n"
                )
            buff.writeIndentedLines(code % inits)
        # create validator object
        code = (
            "# validator object for %(name)s\n"
            "%(name)s = phd.PhotodiodeValidator(\n"
            "    win, %(name)sDiode, %(channel)s,\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)
        # connect stimuli
        for stim in self.findConnectedStimuli():
            code = (
                "# connect {stim} to %(name)s\n"
                "%(name)s.connectStimulus({stim})\n"
            ).format(stim=stim.params['name'])
            buff.writeIndentedLines(code % inits)

    def writeRoutineStartValidationCode(self, buff, stim):
        """
        Write the routine start code to validate a given stimulus using this validator.

        Parameters
        ----------
        buff : StringIO
            String buffer to write code to.
        stim : BaseComponent
            Stimulus to validate

        Returns
        -------
        int
            Change in indentation level after writing
        """
        # get starting indent level
        startIndent = buff.indentLevel

        # choose a clock to sync to according to component's params
        if "syncScreenRefresh" in stim.params and stim.params['syncScreenRefresh']:
            clockStr = ""
        else:
            clockStr = "clock=routineTimer"
        # sync component start/stop timers with validator clocks
        code = (
            f"# synchronise device clock for %(name)s with Routine timer\n"
            f"%(name)s.resetTimer({clockStr})\n"
        )
        buff.writeIndentedLines(code % self.params)

        # return change in indent level
        return buff.indentLevel - startIndent

    def writeEachFrameValidationCode(self, buff, stim):
        """
        Write the each frame code to validate a given stimulus using this validator.

        Parameters
        ----------
        buff : StringIO
            String buffer to write code to.
        stim : BaseComponent
            Stimulus to validate

        Returns
        -------
        int
            Change in indentation level after writing
        """
        # get starting indent level
        startIndent = buff.indentLevel

        # validate start time
        code = (
            "# validate {name} start time\n"
            "if {name}.status == STARTED and %(name)s.status == STARTED:\n"
            "    %(name)s.tStart, %(name)s.tStartDelay = %(name)s.validate(state=True, t={name}.tStartRefresh)\n"
            "    if %(name)s.tStart is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.started', %(name)s.tStart)\n"
            "        thisExp.addData('%(name)s.startDelay', %(name)s.tStartDelay)\n"
            )

        # validate stop time
        code = (
            "# validate {name} stop time\n"
            "if {name}.status == FINISHED and %(name)s.status == STARTED:\n"
            "    %(name)s.tStop, %(name)s.tStopDelay = %(name)s.validate(state=False, t={name}.tStopRefresh)\n"
            "    if %(name)s.tStop is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.stopped', %(name)s.tStop)\n"
            "        thisExp.addData('{name}.%(name)s.stopDelay', %(name)s.tStopDelay)\n"
            )
        buff.writeIndentedLines(code.format(**stim.params) % self.params)

        # return change in indent level
        return buff.indentLevel - startIndent

    def findConnectedStimuli(self):
        # list of linked components
        stims = []
        routines = []
        # inspect each Routine
        for emt in self.exp.flow:
            # skip non-standard Routines
            if not isinstance(emt, Routine):
                continue
            # inspect each Component
            for comp in emt:
                # get validators for this component
                compValidator = comp.getValidator()
                # look for self
                if compValidator == self:
                    # if found, add the comp to the list
                    stims.append(comp)
                    # add to list of Routines containing comps
                    if emt not in routines:
                        routines.append(emt)
        # if any rt has two validated comps, warn
        if len(routines) < len(stims):
            alert(3610, obj=self, strFields={'validator': self.name})

        return stims


class ScreenBufferPhotodiodeValidatorBackend(DeviceBackend):
    """
    Adds a basic screen buffer emulation backend for PhotodiodeValidator, as well as acting as an
    example for implementing other light sensor device backends.
    """

    key = "screenbuffer"
    label = _translate("Screen Buffer (Debug)")
    component = VisualValidatorRoutine
    deviceClasses = ["psychopy.hardware.photodiode.ScreenBufferSampler"]

    def getParams(self: VisualValidatorRoutine):
        # define order
        order = [
        ]
        # define params
        params = {}

        return params, order

    def addRequirements(self):
        # no requirements needed - so just return
        return

    def writeDeviceCode(self: VisualValidatorRoutine, buff):
        # get inits
        inits = getInitVals(self.params)
        # make ButtonGroup object
        code = (
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy.hardware.photodiode.ScreenBufferSampler',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    win=win,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)
