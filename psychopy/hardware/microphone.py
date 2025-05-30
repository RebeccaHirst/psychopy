import sys
import time

import numpy as np
from psychtoolbox import audio as audio
from psychopy import logging as logging, prefs, core
from psychopy.hardware.exceptions import DeviceNotConnectedError
from psychopy.localization import _translate
from psychopy.constants import NOT_STARTED
from psychopy.hardware import BaseDevice, BaseResponse, BaseResponseDevice
from psychopy.sound.audiodevice import AudioDeviceInfo, AudioDeviceStatus
from psychopy.sound.audioclip import AudioClip
from psychopy.sound.exceptions import AudioInvalidCaptureDeviceError, AudioInvalidDeviceError, \
    AudioStreamError, AudioRecordingBufferFullError
from psychopy.tools import systemtools as st
from psychopy.tools.audiotools import SAMPLE_RATE_48kHz


_hasPTB = True
try:
    import psychtoolbox.audio as audio
except (ImportError, ModuleNotFoundError):
    logging.warning(
        "The 'psychtoolbox' library cannot be loaded but is required for audio "
        "capture (use `pip install psychtoolbox` to get it). Microphone "
        "recording will be unavailable this session. Note that opening a "
        "microphone stream will raise an error.")
    _hasPTB = False


class MicrophoneResponse(BaseResponse):
    pass


class MicrophoneDevice(BaseDevice, aliases=["mic", "microphone"]):
    """Class for recording audio from a microphone or input stream.

    Creating an instance of this class will open a stream using the specified
    device. Streams should remain open for the duration of your session. When a
    stream is opened, a buffer is allocated to store samples coming off it.
    Samples from the input stream will writen to the buffer once
    :meth:`~MicrophoneDevice.start()` is called.

    Parameters
    ----------
    index : int or `~psychopy.sound.AudioDevice`
        Audio capture device to use. You may specify the device either by index
        (`int`) or descriptor (`AudioDevice`).
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=48000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in).
    channels : int
        Number of channels to record samples to `1=Mono` and `2=Stereo`.
    streamBufferSecs : float
        Stream buffer size to pre-allocate for the specified number of seconds.
        The default is 2.0 seconds which is usually sufficient.
    maxRecordingSize : int
        Maximum recording size in kilobytes (Kb). Since audio recordings tend to
        consume a large amount of system memory, one might want to limit the
        size of the recording buffer to ensure that the application does not run
        out of memory. By default, the recording buffer is set to 24000 KB (or
        24 MB). At a sample rate of 48kHz, this will result in 62.5 seconds of
        continuous audio being recorded before the buffer is full. You may 
        specify how to handle the buffer when it is full using the 
        `policyWhenFull` parameter.
    policyWhenFull : str
        Policy to use when the recording buffer is full. Options are:
        - "ignore": When full, just don't record any new samples
        - "warn"/"warning": Same as ignore, but will log a warning
        - "error": When full, will raise an error
    audioLatencyMode : int or None
        Audio latency mode to use, values range between 0-4. If `None`, the
        setting from preferences will be used. Using `3` (exclusive mode) is
        adequate for most applications and required if using WASAPI on Windows
        for other settings (such audio quality) to take effect. Symbolic
        constants `psychopy.sound.audiodevice.AUDIO_PTB_LATENCY_CLASS_` can also
        be used.
    audioRunMode : int
        Run mode for the recording device. Default is standby-mode (`0`) which
        allows the system to put the device to sleep. However, when the device
        is needed, waking the device results in some latency. Using a run mode
        of `1` will keep the microphone running (or 'hot') with reduces latency
        when th recording is started. Cannot be set when after initialization at
        this time.

    Examples
    --------
    Capture 10 seconds of audio from the primary microphone::

        import psychopy.core as core
        import psychopy.sound.microphone.Microphone as Microphone

        mic = Microphone(bufferSecs=10.0)  # open the microphone
        mic.start()  # start recording
        core.wait(10.0)  # wait 10 seconds
        mic.stop()  # stop recording

        audioClip = mic.getRecording()

        print(audioClip.duration)  # should be ~10 seconds
        audioClip.save('test.wav')  # save the recorded audio as a 'wav' file

    The prescribed method for making long recordings is to poll the stream once
    per frame (or every n-th frame)::

        mic = Microphone(bufferSecs=2.0)
        mic.start()  # start recording

        # main trial drawing loop
        mic.poll()
        win.flip()  # calling the window flip function

        mic.stop()  # stop recording
        audioClip = mic.getRecording()

    """
    # Force the use of WASAPI for audio capture on Windows. If `True`, only
    # WASAPI devices will be returned when calling static method
    # `Microphone.getDevices()`
    enforceWASAPI = True
    # other instances of MicrophoneDevice, stored by index
    _streams = {}

    def __init__(
            self,
            index=None,
            sampleRateHz=None,
            channels=None,
            streamBufferSecs=2.0,
            maxRecordingSize=-1,
            policyWhenFull='warn',
            exclusive=False,
            audioRunMode=1,
            # legacy
            audioLatencyMode=None,
        ):

        if not _hasPTB:  # fail if PTB is not installed
            raise ModuleNotFoundError(
                "Microphone audio capture requires package `psychtoolbox` to "
                "be installed.")

        from psychopy.hardware import DeviceManager

        # numericise index if needed
        if isinstance(index, str):
            try:
                index = int(index)
            except ValueError:
                pass

        # get information about the selected device
        if isinstance(index, AudioDeviceInfo):
            # if already an AudioDeviceInfo object, great!
            self._device = index
        elif index in (-1, None):
            # get all devices
            _devices = MicrophoneDevice.getDevices()
            # if there are none, error
            if not len(_devices):
                raise DeviceNotConnectedError(
                    _translate(
                        "Could not choose default recording device as no recording "
                        "devices are connected."
                    ), 
                    deviceClass=MicrophoneDevice
                )

            # Try and get the best match which are compatible with the user's
            # specified settings.
            if sampleRateHz is not None or channels is not None:
                self._device = self.findBestDevice(
                    index=_devices[0].deviceIndex,  # use first that shows up
                    sampleRateHz=sampleRateHz,
                    channels=channels
                )
            else:
                self._device = _devices[0]
            
            # Check if the default device settings are differnt than the ones 
            # specified by the user, if so, warn them that the default device
            # settings are overwriting their settings.
            if channels is None:
                channels = self._device.inputChannels
            elif channels != self._device.inputChannels:
                logging.warning(
                    "Number of channels specified ({}) does not match the "
                    "default device's number of input channels ({}).".format(
                        channels, self._device.inputChannels))
                channels = self._device.inputChannels

            if sampleRateHz is None:
                sampleRateHz = self._device.defaultSampleRate
            elif sampleRateHz != self._device.defaultSampleRate:
                logging.warning(
                    "Sample rate specified ({}) does not match the default "
                    "device's sample rate ({}).".format(
                        sampleRateHz, self._device.defaultSampleRate))
                sampleRateHz = self._device.defaultSampleRate

        elif isinstance(index, str):
            # if given a str that's a name from DeviceManager, get info from device
            device = DeviceManager.getDevice(index)
            # try to duplicate and fail if not found
            if isinstance(device, MicrophoneDevice):
                self._device = device._device
            else:
                # if not found, find best match
                self._device = self.findBestDevice(
                    index=index,
                    sampleRateHz=sampleRateHz,
                    channels=channels
                )
        else:
            # get best match
            self._device = self.findBestDevice(
                index=index,
                sampleRateHz=sampleRateHz,
                channels=channels
            )

        devInfoText = ('Using audio device #{} ({}) for audio capture. '
            'Full spec: {}').format(
                self._device.deviceIndex, 
                self._device.deviceName, 
                self._device)
        
        logging.info(devInfoText)

        # error if specified device is not suitable for capture
        if not self._device.isCapture:
            raise AudioInvalidCaptureDeviceError(
                'Specified audio device not suitable for audio recording. '
                'Has no input channels.')

        # get these values from the configured device
        self._channels = self._device.inputChannels
        logging.debug('Set recording channels to {} ({})'.format(
            self._channels, 'stereo' if self._channels > 1 else 'mono'))

        self._sampleRateHz = self._device.defaultSampleRate
        logging.debug('Set stream sample rate to {} Hz'.format(
            self._sampleRateHz))

        # set the audio latency mode
        if exclusive:
            self._audioLatencyMode = 2
        else:
            self._audioLatencyMode = 1
        logging.debug(
            'Set audio latency mode to {}'.format(self._audioLatencyMode)
        )

        # internal recording buffer size in seconds
        assert isinstance(streamBufferSecs, (float, int))
        self._streamBufferSecs = float(streamBufferSecs)

        # PTB specific stuff
        self._mode = 2  # open a stream in capture mode

        # get audio run mode
        assert isinstance(audioRunMode, (float, int)) and \
               (audioRunMode == 0 or audioRunMode == 1)
        self._audioRunMode = int(audioRunMode)

        # open stream
        self._stream = None
        self._opening = self._closing = False
        self.open()

        # status flag for Builder
        self._statusFlag = NOT_STARTED

        # recording buffer information
        self._recording = []  # use a list
        self._totalSamples = 0
        self._maxRecordingSize = (
            -1 if maxRecordingSize is None else int(maxRecordingSize))
        self._policyWhenFull = policyWhenFull

        # internal state
        self._possiblyAsleep = False
        self._isStarted = False  # internal state

        logging.debug('Audio capture device #{} ready'.format(
            self._device.deviceIndex))

        # list to store listeners in
        self.listeners = []
    
    @property
    def maxRecordingSize(self):
        """
        Until a file is saved, the audio data from a Microphone needs to be stored in RAM. To avoid 
        a memory leak, we limit the amount which can be stored by a single Microphone object. The 
        `maxRecordingSize` parameter defines what this limit is.

        Parameters
        ----------
        value : int
            How much data (in kb) to allow, default is 24mb (so 24,000kb)
        """
        return self._maxRecordingSize
    
    @maxRecordingSize.setter
    def maxRecordingSize(self, value):
        self._maxRecordingSize = int(value)
    
    @property
    def policyWhenFull(self):
        """
        Until a file is saved, the audio data from a Microphone needs to be stored in RAM. To avoid 
        a memory leak, we limit the amount which can be stored by a single Microphone object. The 
        `policyWhenFull` parameter tells the Microphone what to do when it's reached that limit.

        Parameters
        ----------
        value : str
            One of:
            - "ignore": When full, just don't record any new samples
            - "warn"/"warning": Same as ignore, but will log a warning
            - "error": When full, will raise an error
            - "roll"/"rolling": When full, clears the start of the buffer to make room for new samples
        """
        return self._policyWhenFull
    
    @policyWhenFull.setter
    def policyWhenFull(self, value):
        self._policyWhenFull = value

    def findBestDevice(self, index, sampleRateHz, channels):
        """
        Find the closest match among the microphone profiles listed by psychtoolbox as valid.

        Parameters
        ----------
        index : int
            Index of the device
        sampleRateHz : int
            Sample rate of the device
        channels : int
            Number of audio channels in input stream

        Returns
        -------
        AudioDeviceInfo
            Device info object for the chosen configuration

        Raises
        ------
        logging.Warning
            If an exact match can't be found, will use the first match to the device index and
            raise a warning.
        KeyError
            If no match is found whatsoever, will raise a KeyError
        """
        # start off with no chosen device and no fallback
        fallbackDevice = None
        chosenDevice = None
        # iterate through device profiles
        for profile in self.getDevices():
            # if same index, keep as fallback
            if index in (profile.deviceIndex, profile.deviceName):
                fallbackDevice = profile
            # if same everything, we got it!
            if all((
                index in (profile.deviceIndex, profile.deviceName),
                profile.defaultSampleRate == sampleRateHz,
                profile.inputChannels == channels,
            )):
                chosenDevice = profile

        if chosenDevice is None and fallbackDevice is not None:
            # if no exact match found, use fallback and raise warning
            logging.warning(
                f"Could not find exact match for specified parameters (index={index}, sampleRateHz="
                f"{sampleRateHz}, channels={channels}), falling back to best approximation ("
                f"index={fallbackDevice.deviceIndex}, "
                f"name={fallbackDevice.deviceName},"
                f"sampleRateHz={fallbackDevice.defaultSampleRate}, "
                f"channels={fallbackDevice.inputChannels})"
            )
            chosenDevice = fallbackDevice
        elif chosenDevice is None:
            # if no index match found, raise error
            raise DeviceNotConnectedError(
                _translate(
                    "Could not find any audio recording device with index {index}", 
                ).format(index=index), 
                deviceClass=MicrophoneDevice
            )

        return chosenDevice

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical microphone as a given other
        object.

        Parameters
        ----------
        other : MicrophoneDevice, dict
            Other MicrophoneDevice to compare against, or a dict of params (which must include
            `index` as a key)

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, type(self)):
            # if given another object, get index
            index = other.index
        elif isinstance(other, dict) and "index" in other:
            # if given a dict, get index from key
            index = other['index']
        else:
            # if the other object is the wrong type or doesn't have an index, it's not this
            return False

        return index in (self.index, self._device.deviceName)

    @staticmethod
    def getDevices():
        """Get a `list` of audio capture device (i.e. microphones) descriptors.
        On Windows, only WASAPI devices are used.

        Returns
        -------
        list
            List of `AudioDevice` descriptors for suitable capture devices. If
            empty, no capture devices have been found.

        """
        try:
            MicrophoneDevice.enforceWASAPI = bool(prefs.hardware["audioForceWASAPI"])
        except KeyError:
            pass  # use default if option not present in settings

        # query PTB for devices
        if MicrophoneDevice.enforceWASAPI and sys.platform == 'win32':
            allDevs = audio.get_devices(device_type=13)
        else:
            allDevs = audio.get_devices()

        # make sure we have an array of descriptors
        allDevs = [allDevs] if isinstance(allDevs, dict) else allDevs

        # create list of descriptors only for capture devices
        devObjs = [AudioDeviceInfo.createFromPTBDesc(dev) for dev in allDevs]
        inputDevices = [desc for desc in devObjs if desc.isCapture]

        return inputDevices

    @staticmethod
    def getAvailableDevices():
        devices = []
        for profile in st.getAudioCaptureDevices():
            # get index as a name if possible
            index = profile.get('device_name', None)
            if index is None:
                index = profile.get('index', None)
            device = {
                'deviceName': profile.get('device_name', "Unknown Microphone"),
                'index': index,
                'sampleRateHz': profile.get('defaultSampleRate', None),
                'channels': profile.get('inputChannels', None),
            }
            devices.append(device)

        return devices

    # def warmUp(self):
    #     """Warm-/wake-up the audio stream.
    #
    #     On some systems the first time `start` is called incurs additional
    #     latency, whereas successive calls do not. To deal with this, it is
    #     recommended that you run this warm-up routine prior to capturing audio
    #     samples. By default, this routine is called when instancing a new
    #     microphone object.
    #
    #     """
    #     # We should put an actual test here to see if timing stabilizes after
    #     # multiple invocations of this function.
    #     self._stream.start()
    #     self._stream.stop()

    @property
    def channels(self):
        """Number of audio channels to record samples to (`int`).
        """
        return self._channels
    
    @property
    def sampleRateHz(self):
        """Sampling rate for audio recording in Hertz (`int`).
        """
        return self._sampleRateHz
    
    @property
    def device(self):
        """Audio device descriptor (`AudioDeviceInfo`).
        """
        return self._device

    @property
    def recording(self):
        """Reference to the current recording buffer (`RecordingBuffer`)."""
        return self._recording

    @property
    def recBufferSecs(self):
        """Capacity of the recording buffer in seconds (`float`)."""
        return self._totalSamples / float(self._sampleRateHz)

    @property
    def latencyBias(self):
        """Latency bias to add when starting the microphone (`float`).
        """
        return self._stream.latency_bias

    @latencyBias.setter
    def latencyBias(self, value):
        self._stream.latency_bias = float(value)

    @property
    def audioLatencyMode(self):
        """Audio latency mode in use (`int`). Cannot be set after
        initialization.

        """
        return self._audioLatencyMode

    @property
    def streamBufferSecs(self):
        """Size of the internal audio storage buffer in seconds (`float`).

        To ensure all data is captured, there must be less time elapsed between
        subsequent `getAudioClip` calls than `bufferSecs`.

        """
        return self._streamBufferSecs

    @property
    def streamStatus(self):
        """Status of the audio stream (`AudioDeviceStatus` or `None`).

        See :class:`~psychopy.sound.AudioDeviceStatus` for a complete overview
        of available status fields. This property has a value of `None` if
        the stream is presently closed.

        Examples
        --------
        Get the capture start time of the stream::

            # assumes mic.start() was called
            captureStartTime = mic.status.captureStartTime

        Check if microphone recording is active::

            isActive = mic.status.active

        Get the number of seconds recorded up to this point::

            recordedSecs = mic.status.recordedSecs

        """
        currentStatus = self._stream.status
        if currentStatus != -1:
            return AudioDeviceStatus.createFromPTBDesc(currentStatus)

    @property
    def isRecBufferFull(self):
        """`True` if there is an overflow condition with the recording buffer.

        If this is `True`, then `poll()` is still collecting stream samples but
        is no longer writing them to anything, causing stream samples to be
        lost.

        """
        return self._totalSamples >= self._maxRecordingSize

    @property
    def isStarted(self):
        """``True`` if stream recording has been started (`bool`)."""
        return self._isStarted

    @property
    def isRecording(self):
        """``True`` if stream recording has been started (`bool`). Alias of
        `isStarted`."""
        return self.isStarted

    @property
    def index(self):
        return self._device.deviceIndex

    def testDevice(self, duration=1, testSound=None):
        """
        Make a recording to test the microphone.

        Parameters
        ----------
        duration : float, int
            How long to record for? In seconds.
        testSound : str, AudioClip, None
            Sound to play to test mic. Use "sine", "square" or "sawtooth" to generate a sound of correct
            duration using AudioClip. Use None to not play a test sound.

        Returns
        -------
        bool
            True if test passed. On fail, will log the error at level "debug".
        """
        # if given a string for testSound, generate
        if testSound in ("sine", "square", "sawtooth"):
            testSound = getattr(AudioClip, testSound)(duration=duration)

        try:
            # record
            self.start(stopTime=duration)
            # play testSound
            if testSound is not None:
                from psychopy.sound import Sound
                snd = Sound(value=testSound)
                snd.play()
            # sleep for duration
            time.sleep(duration)
            # poll to refresh recording
            self.poll()
            # get new clip
            clip = self.getRecording()
            # check that clip matches test sound
            if testSound is not None:
                # todo: check the recording against testSound
                pass

            return True

        except Exception as err:
            logging.debug(f"Microphone test failed. Error: {err}")

            raise err

    def start(self, when=None, waitForStart=0, stopTime=None):
        """Start an audio recording.

        Calling this method will begin capturing samples from the microphone and
        writing them to the buffer.

        Parameters
        ----------
        when : float, int or None
            When to start the stream. If the time specified is a floating point
            (absolute) system time, the device will attempt to begin recording
            at that time. If `None` or zero, the system will try to start
            recording as soon as possible.
        waitForStart : bool
            Wait for sound onset if `True`.
        stopTime : float, int or None
            Number of seconds to record. If `None` or `-1`, recording will
            continue forever until `stop` is called.

        Returns
        -------
        float
            Absolute time the stream was started.

        """
        # check if the stream has been
        if self.isStarted:
            return None

        if self._stream is None:
            raise AudioStreamError("Stream not ready.")
        # reset timer for possibly asleep
        self._possiblyAsleep = False
        # reset the recording buffer
        self._recording = []
        self._totalSamples = 0

        # reset warnings
        # self._warnedRecBufferFull = False

        startTime = self._stream.start(
            repetitions=0,
            when=when,
            wait_for_start=int(waitForStart),
            stop_time=stopTime)

        # recording has begun or is scheduled to do so
        self._isStarted = True

        logging.debug(
            'Scheduled start of audio capture for device #{} at t={}.'.format(
                self._device.deviceIndex, startTime))

        return startTime

    def record(self, when=None, waitForStart=0, stopTime=None):
        """Start an audio recording (alias of `.start()`).

        Calling this method will begin capturing samples from the microphone and
        writing them to the buffer.

        Parameters
        ----------
        when : float, int or None
            When to start the stream. If the time specified is a floating point
            (absolute) system time, the device will attempt to begin recording
            at that time. If `None` or zero, the system will try to start
            recording as soon as possible.
        waitForStart : bool
            Wait for sound onset if `True`.
        stopTime : float, int or None
            Number of seconds to record. If `None` or `-1`, recording will
            continue forever until `stop` is called.

        Returns
        -------
        float
            Absolute time the stream was started.

        """
        return self.start(
            when=when,
            waitForStart=waitForStart,
            stopTime=stopTime)

    def stop(self, blockUntilStopped=True, stopTime=None):
        """Stop recording audio.

        Call this method to end an audio recording if in progress. This will
        simply halt recording and not close the stream. Any remaining samples
        will be polled automatically and added to the recording buffer.

        Parameters
        ----------
        blockUntilStopped : bool
            Halt script execution until the stream has fully stopped.
        stopTime : float or None
            Scheduled stop time for the stream in system time. If `None`, the
            stream will stop as soon as possible.

        Returns
        -------
        tuple or None
            Tuple containing `startTime`, `endPositionSecs`, `xruns` and
            `estStopTime`. Returns `None` if `stop` or `pause` was called
            previously before `start`.

        """
        # This function must be idempotent since it can be invoked at any time
        # whether a stream is started or not.
        if not self.isStarted or self._stream._closed:
            return

        # poll remaining samples, if any
        self.poll()

        startTime, endPositionSecs, xruns, estStopTime = self._stream.stop(
            block_until_stopped=int(blockUntilStopped),
            stopTime=stopTime)
        self._isStarted = False

        logging.debug(
            ('Device #{} stopped capturing audio samples at estimated time '
             't={}. Total overruns: {} Total recording time: {}').format(
                self._device.deviceIndex, estStopTime, xruns, endPositionSecs))

        return startTime, endPositionSecs, xruns, estStopTime

    def pause(self, blockUntilStopped=True, stopTime=None):
        """Pause a recording (alias of `.stop`).

        Call this method to end an audio recording if in progress. This will
        simply halt recording and not close the stream. Any remaining samples
        will be polled automatically and added to the recording buffer.

        Parameters
        ----------
        blockUntilStopped : bool
            Halt script execution until the stream has fully stopped.
        stopTime : float or None
            Scheduled stop time for the stream in system time. If `None`, the
            stream will stop as soon as possible.

        Returns
        -------
        tuple or None
            Tuple containing `startTime`, `endPositionSecs`, `xruns` and
            `estStopTime`. Returns `None` if `stop()` or `pause()` was called
            previously before `start()`.

        """
        return self.stop(blockUntilStopped=blockUntilStopped, stopTime=stopTime)

    def open(self):
        """
        Open the audio stream.
        """
        # do nothing if stream is already open
        if self._stream is not None and not self._stream._closed:
            return
        # set flag that it's mid-open
        self._opening = True
        # search for open streams and if there is one, use it
        if self._device.deviceIndex in MicrophoneDevice._streams:
            logging.debug(
                f"Assigning audio stream for device #{self._device.deviceIndex} to a new "
                f"MicrophoneDevice object."
            )
            self._stream = MicrophoneDevice._streams[self._device.deviceIndex]
            return
        
        # if no open streams, make one
        logging.debug(
            f"Opening new audio stream for device #{self._device.deviceIndex}."
        )
        self._stream = MicrophoneDevice._streams[self._device.deviceIndex] = audio.Stream(
            device_id=self._device.deviceIndex,
            latency_class=self._audioLatencyMode,
            mode=self._mode,
            freq=self._device.defaultSampleRate,
            channels=self._device.inputChannels
        )
        # set run mode
        self._stream.run_mode = self._audioRunMode
        logging.debug('Set run mode to `{}`'.format(
            self._audioRunMode))
        # set latency bias
        self._stream.latency_bias = 0.0
        logging.debug('Set stream latency bias to {} ms'.format(
            self._stream.latency_bias))
        # pre-allocate recording buffer, called once
        self._stream.get_audio_data(self._streamBufferSecs)
        logging.debug(
            'Allocated stream buffer to hold {} seconds of data'.format(
                self._streamBufferSecs))
        # set flag that it's done opening
        self._opening = False
        
    def close(self):
        """
        Close the audio stream.
        """
        # clear any attached listeners
        self.clearListeners()
        # do nothing further if already closed
        if self._stream._closed:
            return
        # set flag that it's mid-close
        self._closing = True
        # remove ref to stream
        if self._device.deviceIndex in MicrophoneDevice._streams:
            MicrophoneDevice._streams.pop(self._device.deviceIndex)
        # close stream
        self._stream.close()
        logging.debug('Stream closed')
        # set flag that it's done closing
        self._closing = False
    
    def reopen(self):
        """
        Calls self.close() then self.open() to reopen the stream.
        """
        # get status at close
        status = self.isStarted
        # start timer
        start = time.time()
        # close then open
        self.close()
        self.open()
        # log time it took
        logging.info(
            f"Reopened microphone #{self.index}, took {time.time() - start:.3f}s"
        )
        # if mic was running beforehand, start it back up again now
        if status:
            self.start()

    @property
    def recordingEmpty(self):
        """`True` if the recording buffer is empty (`bool`).
        """
        return len(self._recording) == 0
    
    @property
    def recordingFull(self):
        """`True` if the recording buffer is full (`bool`).
        """
        if self._maxRecordingSize < 0:
            return False
        return self._totalSamples >= self._maxRecordingSize

    def poll(self):
        """Poll audio samples.

        Calling this method adds audio samples collected from the stream buffer
        to the recording buffer that have been captured since the last `poll`
        call. Time between calls of this function should be less than
        `bufferSecs`. You do not need to call this if you call `stop` before
        the time specified by `bufferSecs` elapses since the `start` call.

        Can only be called between called of `start` (or `record`) and `stop`
        (or `pause`).

        Returns
        -------
        int
            Number of overruns in sampling.

        """
        if not self.isStarted:
            logging.warning(
                "Attempted to poll samples from mic which hasn't started."
            )
            return
        if self._stream._closed:
            logging.warning(
                "Attempted to poll samples from mic which has been closed."
            )
            return
        if self._opening or self._closing:
            action = "opening" if self._opening else "closing"
            logging.warning(
                f"Attempted to poll microphone while the stream was still {action}. Samples will be "
                f"lost."
            )
            return

        # figure out what to do with this other information
        audioData, absRecPosition, overflow, cStartTime = \
            self._stream.get_audio_data()
        
        if len(audioData):
            # if we got samples, the device is awake, so stop figuring out if it's asleep
            self._possiblyAsleep = False
        elif self._possiblyAsleep is False:
            # if it was awake and now we've got no samples, store the time
            self._possiblyAsleep = time.time()
        elif self._possiblyAsleep + 1 < time.time():
            # if we've not had any evidence of it being awake for 1s, reopen
            logging.error(
                f"Microphone device appears to have gone to sleep, reopening to wake it up."
            )
            # mark as stopped so we don't recursively poll forever when stopping
            self._isStarted = False
            # reopen
            self.reopen()
            # start again
            self.start()
            # mark as not asleep so we don't restart again if the first poll is empty
            self._possiblyAsleep = False

        if overflow:
            logging.warning(
                "Audio stream buffer overflow, some audio samples have been "
                "lost! To prevent this, ensure `Microphone.poll()` is being "
                "called often enough, or increase the size of the audio buffer "
                "with `bufferSecs`.")

        # add samples to recording buffer
        if len(audioData):
            # add samples to recording buffer
            self._recording.append(
                AudioClip(audioData, sampleRateHz=self._sampleRateHz))
            self._totalSamples += audioData.shape[0]

        if self.recordingFull and not self._policyWhenFull == 'ignore':
            if self._policyWhenFull == 'warn':
                logging.warning(
                    "Recording buffer is full, no more samples will be added.")
            elif self._policyWhenFull == 'error':
                raise AudioStreamError(
                    "Recording buffer is full, no more samples will be added.")

        return 0
    
    def _mergeAudioFragments(self):
        """Merge audio fragments into a single segment.
        
        This merges all audio fragments in the recoding buffer into a single
        `AudioClip` object. The recording buffer is then cleared and the first
        element is set to the merged segment.

        Returns
        -------
        bool
            `False` if the recording buffer has no fragments to merge, `True`
            otherwise.

        """
        if len(self._recording) < 2:
            return False
        
        # get the sum of all audio samples in the recording buffer
        totalSamples = sum(
            [segment.samples.shape[0] for segment in self._recording])

        # create a new array to hold all samples
        fullSegment = np.zeros(
            (totalSamples, self._recording[0].channels), 
            dtype=np.float32, 
            order='C')
        
        # copy samples from each segment into the full segment
        idx = 0
        for segment in self._recording:
            nSamples = segment.samples.shape[0]
            fullSegment[idx:idx + nSamples, :] = segment.samples
            idx += nSamples

        # set the recording
        self._recording = [
            AudioClip(fullSegment, sampleRateHz=self._sampleRateHz)]  

        return True
    
    def _getSegment(self, start=0, end=None):
        """Get a segment of audio samples from the recording buffer.

        Parameters
        ----------
        start : float
            Start time of the segment in seconds.
        end : float or None
            End time of the segment in seconds. If `None`, the segment will
            extend to the end of the recording buffer.

        Returns
        -------
        AudioClip or None
            Segment of the recording buffer. Returns `None` if the recording
            buffer is empty.

        """
        if self.recordingEmpty:
            return None
        
        self._mergeAudioFragments()  # merge audio fragments

        if not len(self._recording[0].samples):
            raise AudioStreamError(
                "Could not access recording as microphone has sent no samples."
            )
        
        if start == 0 and end is None:  # return full recording
            return self._recording[0]

        # get a range of samples within the recording buffer
        idxStart = int(start * self._sampleRateHz)
        idxEnd = -1 if end is None else int(end * self._sampleRateHz)
        
        return AudioClip(
            np.array(self._recording[0].samples[idxStart:idxEnd, :],
                     dtype=np.float32, order='C'),
            sampleRateHz=self._sampleRateHz)

    def getRecording(self):
        """Get audio data from the last microphone recording.

        Call this after `stop` to get the recording as an `AudioClip` object.
        Raises an error if a recording is in progress.

        Returns
        -------
        AudioClip
            Recorded data between the last calls to `start` (or `record`) and
            `stop`.

        """
        if self.isStarted:
            logging.warn(
                "Cannot get audio clip while recording is in progress, so "
                "stopping recording now."
            )
            self.stop()

        # get the segment
        return self._getSegment()  # full recording
    
    def getCurrentVolume(self, timeframe=0.2):
        """
        Get the current volume measured by the mic.

        Parameters
        ----------
        timeframe : float
            Time frame (s) over which to take samples from. Default is 0.1s.

        Returns
        -------
        float
            Current volume registered by the mic, will depend on relative volume 
            of the mic but should mostly be between 0 (total silence) and 1 
            (very loud).

        """
        # if mic hasn't started yet, return 0 as it's recorded nothing
        if not self.isStarted or self._stream._closed:
            return 0
        
        # poll most recent samples
        self.poll()

        if self.recordingEmpty:
            return 0.0

        # merge last few recording fragments into a single segment
        requiredSamples = int(timeframe * self._sampleRateHz)
        sampleBuffers = []
        for segment in reversed(self._recording):
            nSamples = segment.samples.shape[0]
            requiredSamples -= nSamples
            if requiredSamples < 0:
                sampleBuffers.insert(0, segment.samples[requiredSamples:, :])
                break
            sampleBuffers.insert(0, segment.samples)

        # merge the samples
        sampleBuffer = np.concatenate(
            sampleBuffers, axis=0, dtype=np.float32)

        clip = AudioClip(sampleBuffer, sampleRateHz=self._sampleRateHz)

        # get average volume
        rms = clip.rms() * 10

        # round
        rms = np.round(rms.astype(np.float64), decimals=3)

        return rms

    def addListener(self, listener, startLoop=False):
        """
        Add a listener, which will receive all the same messages as this device.

        Parameters
        ----------
        listener : str or psychopy.hardware.listener.BaseListener
            Either a Listener object, or use one of the following strings to create one:
            - "liaison": Create a LiaisonListener with DeviceManager.liaison as the server
            - "print": Create a PrintListener with default settings
            - "log": Create a LoggingListener with default settings
        startLoop : bool
            If True, then upon adding the listener, start up an asynchronous loop to dispatch messages.
        """
        # add listener as normal
        listener = BaseResponseDevice.addListener(self, listener, startLoop=startLoop)
        # if we're starting a listener loop, start recording
        if startLoop:
            self.start()
        
        return listener

    def clearListeners(self):
        """
        Remove any listeners from this device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # clear listeners as normal
        resp = BaseResponseDevice.clearListeners(self)
        # stop recording
        self.stop()

        return resp

    def dispatchMessages(self, clear=True):
        """
        Dispatch current volume as a MicrophoneResponse object to any attached listeners.

        Parameters
        ----------
        clear : bool
            If True, will clear the recording up until now after dispatching the volume. This is
            useful if you're just sampling volume and aren't wanting to store the recording.
        """
        # if mic is not recording, there's nothing to dispatch
        if not self.isStarted:
            return
        
        # poll the mic now
        self.poll()
        # create a response object
        message = MicrophoneResponse(
            logging.defaultClock.getTime(),
            self.getCurrentVolume(),
            device=self,
        )
        # dispatch to listeners
        for listener in self.listeners:
            listener.receiveMessage(message)
        
        return message
    
    def findSpeakers(self, allowedSpeakers=None, threshold=0.01):
        """
        Find speakers which this microphone can hear.

        Parameters
        ----------
        allowedSpeakers : list[SpeakerDevice or dict] or None
            List of speakers to test, or leave as None to test all speakers. If speakers are given 
            as a dict, SpeakerDevice objects will be created via DeviceManager. 
        threshold : float
            Necessary difference in volume (dB) between sound playing and not playing to conclude 
            that this mic can hear the given speaker.

        Returns
        -------
        list[SpeakerDevice]
            List of speakers which this MicrophoneDevice can hear
        """
        from psychopy import sound
        from psychopy.hardware import DeviceManager

        def _takeReading(dur):
            """
            Take a reading from this MicrophoneDevice and return the average volume.

            Parameters
            ----------
            dur : float
                Time (s) to read for

            Returns
            -------
            float
                Average volume across samples and channels during the reading
            """
            # countdown for the duration
            countdown = core.CountdownTimer(dur)
            # start recording
            self.start()
            # poll while active
            while countdown.getTime() > 0:
                self.poll()
            # get volume
            vol = self.getCurrentVolume(timeframe=dur)
            # if multi-channel, take the max
            try:
                vol = max(vol)
            except TypeError:
                pass
            # stop recording
            self.stop()

            return vol
        
        # if no allowed speakers given, use all
        if allowedSpeakers is None:
            allowedSpeakers = DeviceManager.getAvailableDevices(
                "psychopy.hardware.speaker.SpeakerDevice"
            )
        # list of found speakers
        foundSpeakers = []
        # iterate through allowed speakers
        for speaker in allowedSpeakers:
            # if given a dict, actualise it
            if isinstance(speaker, dict):
                speakerProfile = speaker
                speaker = DeviceManager.getDevice(speakerProfile['deviceName'])
                if speaker is None:
                    speaker = DeviceManager.addDevice(**speakerProfile)
            # generate a sound for this speaker
            try:
                snd = sound.Sound("A", stereo=True, speaker=speaker)
            except:
                # silently skip on error
                continue
            # get a baseline volume
            baseline = _takeReading(1)
            # start playing a beep
            snd.play()
            # get an active volume
            active = _takeReading(1)
            # stop the beep
            snd.stop()
            # if the difference is above the threshold, speaker is good
            if active - baseline > threshold:
                foundSpeakers.append(speaker)
        
        return foundSpeakers


class RecordingBuffer:
    """Class for a storing a recording from a stream.

    Think of instances of this class behaving like an audio tape whereas the
    `MicrophoneDevice` class is the tape recorder. Samples taken from the stream are
    written to the tape which stores the data.

    Used internally by the `MicrophoneDevice` class, users usually do not create
    instances of this class themselves.

    Parameters
    ----------
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=48000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in).
    channels : int
        Number of channels to record samples to `1=Mono` and `2=Stereo`.
    maxRecordingSize : int
        Maximum recording size in kilobytes (Kb). Since audio recordings tend to
        consume a large amount of system memory, one might want to limit the
        size of the recording buffer to ensure that the application does not run
        out of memory. By default, the recording buffer is set to 24000 KB (or
        24 MB). At a sample rate of 48kHz, this will result in 62.5 seconds of
        continuous audio being recorded before the buffer is full.
    policyWhenFull : str
        What to do when the recording buffer is full and cannot accept any more
        samples. If 'ignore', samples will be silently dropped and the `isFull`
        property will be set to `True`. If 'warn', a warning will be logged and
        the `isFull` flag will be set. Finally, if 'error' the application will
        raise an exception.

    """
    def __init__(self, sampleRateHz=SAMPLE_RATE_48kHz, channels=2,
                 maxRecordingSize=None, policyWhenFull='ignore'):
        self._channels = channels
        self._sampleRateHz = sampleRateHz
        self._maxRecordingSize = maxRecordingSize or 64000
        self._samples = None  # `ndarray` created in _allocRecBuffer`
        self._offset = 0  # recording offset
        self._lastSample = 0  # offset of the last sample from stream
        self._spaceRemaining = None  # set in `_allocRecBuffer`
        self._totalSamples = None  # set in `_allocRecBuffer`

        self._policyWhenFull = policyWhenFull
        self._warnedRecBufferFull = False
        self._loops = 0

        self._allocRecBuffer()

    def _allocRecBuffer(self):
        """Allocate the recording buffer. Called internally if properties are
        changed."""
        # allocate another array
        nBytes = self._maxRecordingSize * 1000
        recArraySize = int((nBytes / self._channels) / (np.float32()).itemsize)

        self._samples = np.zeros(
            (recArraySize, self._channels), dtype=np.float32, order='C')

        # sanity check
        assert self._samples.nbytes == nBytes
        self._totalSamples = len(self._samples)
        self._spaceRemaining = self._totalSamples

    @property
    def samples(self):
        """Reference to the actual sample buffer (`ndarray`)."""
        return self._samples

    @property
    def bufferSecs(self):
        """Capacity of the recording buffer in seconds (`float`)."""
        return self._totalSamples / self._sampleRateHz

    @property
    def nbytes(self):
        """Number of bytes the recording buffer occupies in memory (`int`)."""
        return self._samples.nbytes

    @property
    def sampleBytes(self):
        """Number of bytes per sample (`int`)."""
        return np.float32().itemsize

    @property
    def spaceRemaining(self):
        """The space remaining in the recording buffer (`int`). Indicates the
        number of samples that the buffer can still add before overflowing.
        """
        return self._spaceRemaining

    @property
    def isFull(self):
        """Is the recording buffer full (`bool`)."""
        return self._spaceRemaining <= 0

    @property
    def totalSamples(self):
        """Total number samples the recording buffer can hold (`int`)."""
        return self._totalSamples

    @property
    def writeOffset(self):
        """Index in the sample buffer where new samples will be written when
        `write()` is called (`int`).
        """
        return self._offset

    @property
    def lastSample(self):
        """Index of the last sample recorded (`int`). This can be used to slice
        the recording buffer, only getting data from the beginning to place
        where the last sample was written to.
        """
        return self._lastSample

    @property
    def loopCount(self):
        """Number of times the recording buffer restarted (`int`). Only valid if
        `loopback` is ``True``."""
        return self._loops

    @property
    def maxRecordingSize(self):
        """Maximum recording size in kilobytes (`int`).

        Since audio recordings tend to consume a large amount of system memory,
        one might want to limit the size of the recording buffer to ensure that
        the application does not run out of memory. By default, the recording
        buffer is set to 24000 KB (or 24 MB). At a sample rate of 48kHz, this
        will result in 62.5 seconds of continuous audio being recorded before
        the buffer is full.

        Setting this value will allocate another recording buffer of appropriate
        size. Avoid doing this in any time sensitive parts of your application.

        """
        return self._maxRecordingSize

    @maxRecordingSize.setter
    def maxRecordingSize(self, value):
        value = int(value)

        # don't do this unless the value changed
        if value == self._maxRecordingSize:
            return

        # if different than last value, update the recording buffer
        self._maxRecordingSize = value
        self._allocRecBuffer()

    def seek(self, offset, absolute=False):
        """Set the write offset.

        Use this to specify where to begin writing samples the next time `write`
        is called. You should call `seek(0)` when starting a new recording.

        Parameters
        ----------
        offset : int
            Position in the sample buffer to set.
        absolute : bool
            Use absolute positioning. Use relative positioning if `False` where
            the value of `offset` will be added to the current offset. Default
            is `False`.

        """
        if not absolute:
            self._offset += offset
        else:
            self._offset = absolute

        assert 0 <= self._offset < self._totalSamples
        self._spaceRemaining = self._totalSamples - self._offset

    def write(self, samples):
        """Write samples to the recording buffer.

        Parameters
        ----------
        samples : ArrayLike
            Samples to write to the recording buffer, usually of a stream. Must
            have the same number of dimensions as the internal array.

        Returns
        -------
        int
            Number of samples overflowed. If this is zero then all samples have
            been recorded, if not, the number of samples rejected is given.

        """
        nSamples = len(samples)
        if self.isFull:
            if self._policyWhenFull in ('warn', 'warning'):
                # if policy is warn, we log a warning then proceed as if ignored
                if not self._warnedRecBufferFull:
                    logging.warning(
                        f"Audio recording buffer filled! This means that no "
                        f"samples are saved beyond {round(self.bufferSecs, 6)} "
                        f"seconds. Specify a larger recording buffer next time "
                        f"to avoid data loss.")
                    logging.flush()
                    self._warnedRecBufferFull = True
                return nSamples
            elif self._policyWhenFull == 'error':
                # if policy is error, we fully error
                raise AudioRecordingBufferFullError(
                    "Cannot write samples, recording buffer is full.")
            elif self._policyWhenFull == ('rolling', 'roll'):
                # if policy is rolling, we clear the first half of the buffer
                toSave = self._totalSamples - len(samples)
                # get last 0.1s so we still have enough for volume measurement
                savedSamples = self._recording._samples[-toSave:, :]
                # log
                if not self._warnedRecBufferFull:
                    logging.warning(
                        f"Microphone buffer reached, as policy when full is 'roll'/'rolling' the "
                        f"oldest samples will be cleared to make room for new samples."
                    )
                    logging.flush()
                self._warnedRecBufferFull = True
                # clear samples
                self._recording.clear()
                # reassign saved samples
                self._recording.write(savedSamples)
            else:
                # if policy is to ignore, we simply don't write new samples
                return nSamples

        if not nSamples:  # no samples came out of the stream, just return
            return

        if self._spaceRemaining >= nSamples:
            self._lastSample = self._offset + nSamples
            audioData = samples[:, :]
        else:
            self._lastSample = self._offset + self._spaceRemaining
            audioData = samples[:self._spaceRemaining, :]

        self._samples[self._offset:self._lastSample, :] = audioData
        self._offset += nSamples

        self._spaceRemaining -= nSamples

        # Check if the recording buffer is now full. Next call to `poll` will
        # not record anything.
        if self._spaceRemaining <= 0:
            self._spaceRemaining = 0

        d = nSamples - self._spaceRemaining
        return 0 if d < 0 else d

    def clear(self):
        # reset all live attributes
        self._samples = None
        self._offset = 0
        self._lastSample = 0
        self._spaceRemaining = None
        self._totalSamples = None
        # reallocate buffer
        self._allocRecBuffer()

    def getSegment(self, start=0, end=None):
        """Get a segment of recording data as an `AudioClip`.

        Parameters
        ----------
        start : float or int
            Absolute time in seconds for the start of the clip.
        end : float or int
            Absolute time in seconds for the end of the clip. If `None` the time
            at the last sample is used.

        Returns
        -------
        AudioClip
            Audio clip object with samples between `start` and `end`.

        """
        idxStart = int(start * self._sampleRateHz)
        idxEnd = self._lastSample if end is None else int(
            end * self._sampleRateHz)
        
        if not len(self._samples):
            raise AudioStreamError(
                "Could not access recording as microphone has sent no samples."
            )

        return AudioClip(
            np.array(self._samples[idxStart:idxEnd, :],
                     dtype=np.float32, order='C'),
            sampleRateHz=self._sampleRateHz)