Installation
===============

.. _download:

Download
-----------

.. tab-set::

  .. tab-item:: Windows

    .. grid:: 1 1 2 2
      :gutter: 2

      .. grid-item-card::  Stable

        Tried and tested, this is the release that's been out in the wild for a bit and has already had any post-release bug fixes it needed. The best option for an install that "just works".

        .. button-link:: https://github.com/psychopy/psychopy/releases/download/2024.2.4/StandalonePsychoPy-2024.2.4-win64-3.10.exe
          :color: primary

          PsychoPy 2024.2.4 (py3.10)
        
        .. dropdown:: Compatibility+ installer (py3.8)

          .. button-link:: https://github.com/psychopy/psychopy/releases/download/2024.2.4/StandalonePsychoPy-2024.2.4-win64-3.8.exe
            :color: primary

            PsychoPy 2024.2.4 compatibility+ (py3.8)
      
      .. grid-item-card::  Beta

        Hot off the presses, this is the latest release with all the newest features. If you're fine with a few bugs so long as you get the cutting edge features as soon as they're ready, this is the install for you.

        .. button-link:: https://github.com/psychopy/psychopy/releases/download/2025.1.0/StandalonePsychoPy-2025.1.0-win64-py3.10.exe
          :color: primary

          PsychoPy 2025.1.0beta (py3.10)
        
        .. dropdown:: Compatibility+ installer (py3.8)

          .. button-link:: https://github.com/psychopy/psychopy/releases/download/2025.1.0/StandalonePsychoPy-2025.1.0-win64-py3.8.exe
            :color: primary

            PsychoPy 2025.1.0 compatibility+ (py3.8)
  
  .. tab-item:: MacOS

    .. grid:: 1 1 2 2
      :gutter: 2

      .. grid-item-card::  Stable

        Tried and tested, this is the release that's been out in the wild for a bit and has already had any post-release bug fixes it needed. The best option for an install that "just works".

        .. button-link:: https://github.com/psychopy/psychopy/releases/download/2024.2.4/StandalonePsychoPy-2024.2.4-macOS-3.10.dmg
          :color: primary

          PsychoPy 2024.2.4 (py3.10)
        
        .. dropdown:: Compatibility+ installer (py3.8)

          .. button-link:: https://github.com/psychopy/psychopy/releases/download/2024.2.4/StandalonePsychoPy-2024.2.4-macOS-3.8.dmg
            :color: primary

            PsychoPy 2024.2.4 compatibility+ (py3.8)
      
      .. grid-item-card::  Beta

        Hot off the presses, this is the latest release with all the newest features. If you're fine with a few bugs so long as you get the cutting edge features as soon as they're ready, this is the install for you.

        .. button-link:: https://github.com/psychopy/psychopy/releases/download/2025.1.0/StandalonePsychoPy-2025.1.0-macOS-py3.10.dmg
          :color: primary

          PsychoPy 2025.1.0beta (py3.10)
        
        .. dropdown:: Compatibility+ installer (py3.8)

          .. button-link:: https://github.com/psychopy/psychopy/releases/download/2025.1.0/StandalonePsychoPy-2025.1.0-macOS-py3.8.dmg
            :color: primary

            PsychoPy 2025.1.0 compatibility+ (py3.8)
  
  .. tab-item:: Linux

    Install curl with your package manager. On most distros, curl is already installed.

      1. **Download the script:**

        .. code-block:: bash
            
          curl -LOs https://github.com/wieluk/psychopy_linux_installer/releases/latest/download/psychopy_linux_installer
      
      2. **Make it executable:**

        .. code-block:: bash
            
          chmod +x psychopy_linux_installer
      
      3. **Run the installer:**

        - **GUI Mode**:

          .. code-block:: bash
              
            ./psychopy_linux_installer --gui
            
          *Note:* `curl` and `zenity` are required for GUI mode.

        - **Command-Line Mode**:

          .. code-block:: bash
              
            ./psychopy_linux_installer
      
      For a list of available arguments, run:

        .. code-block:: bash
            
          ./psychopy_linux_installer --help
      
      For more detailed information or to report bugs, please visit the 
      `psychopy_linux_installer GitHub page <https://github.com/wieluk/psychopy_linux_installer>`_.

.. raw:: html

   <script src="https://cdn.jsdelivr.net/npm/ua-parser-js@1/dist/ua-parser.min.js"></script>
   <script>
      let clientInfo = UAParser(navigator.userAgent);
      var osLabel;
      var arch = clientInfo.cpu.architecture;
      // create the platform dependent strings
      if (navigator.platform == 'Win32' && clientInfo.cpu.architecture == 'amd64') {
         document.getElementById("sd-tab-item-0").checked = true; // Windows
      }
      else if (clientInfo.os.name == 'Mac OS') {
         document.getElementById("sd-tab-item-1").checked = true; // MacOS
      }
      else {
         document.getElementById("sd-tab-item-2").checked = true; // Linux
      }
   </script>

**For all versions** see the `PsychoPy releases on github <https://github.com/psychopy/psychopy/releases>`_

|PsychoPy| is distributed under the `GPL3 license <https://github.com/psychopy/psychopy/blob/master/LICENSE>`_

.. _compatibility_installer:

Do I need the Compatibility+ installer?
-------------------------------------------------
While PsychoPy has supported Python 3.10 since version 2022.2.0, the :ref:`experimentsettings_use-version` parameter in Experiment Settings makes it possible to run an experiment using an older version of the PsychoPy library, including versions from before Python 3.10 was supported - meaning they will fail to run if your installed Python is newer than version 3.8. The Compatibility+ installer installs PsychoPy with Python 3.8, allowing you to run these legacy experiments, but losing out on the speed and stability improvements which come with a newer version of Python. 

We recommend installing via the Compatibility+ installer **only if necessary**, as besides running legacy experiments, PsychoPy will perform faster and better in Python 3.10.

.. _manual_install:

Manual installations
-------------------------------------------------

See below for options if you don't want to use the Standalone releases:

* :ref:`pip_install`
* :ref:`brew_install`
* :ref:`linux_install`
* :ref:`conda`
* :ref:`developers_install`

.. _pip_install:

pip install
~~~~~~~~~~~~~~~~~

Now that most python libraries can be installed using `pip` it's relatively easy
to manually install |PsychoPy| and all it's dependencies to your own installation
of Python.

The steps are to fetch Python. This method should work on a range of versions of Python
but **we strongly recommend you use Python 3.10 or 3.8**. Older Python versions are no longer being tested and
may not work correctly. Newer Python versions may not have wheels for all the necessary
dependencies even though we believe that PsychoPy's code, itself, is compatible up
to at least Python 3.10.

You can install |PsychoPy| and its dependencies (more than you'll strictly need, depending on the features you use)
by::

  pip install psychopy

If you prefer *not* to install *all* the dependencies (e.g. because the platform or Python version you're
on doesn't have that dependency easily available) then you could do::

  pip install psychopy --no-deps

and then install them manually. On Windows, if you need a package that isn't available on PyPI you
may want to try the `unofficial packages by Christoph Gohlke <https://www.lfd.uci.edu/~gohlke/pythonlibs/>`_

.. _brew_install:

brew install
~~~~~~~~~~~~~~~~~

This is a user-contributed option and may or may not work.

On a MacOS machine, `brew` can be used to install |PsychoPy|::

  brew install --cask psychopy

.. _linux_install:

Linux
~~~~~~~~~~~~~~~~~

We are aware that the procedure for installing on Linux is often rather painful.
This is not the platform that the core PsychoPy developers currently use so support
is less good than on some platforms. Feel free to jump in and help improve it as a
contributor! :-)

There used to be neurodebian and Gentoo packages for |PsychoPy| but these are both
badly outdated. We'd recommend you first make sure you have a compatible Python
version installed (currently ``>=3.8, <3.11``). If you need an older version, you
can on Ubuntu for example do:

.. code-block:: bash

    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.10-venv python3.10-dev
    python3.10 -m venv path/to/new/psychopyenv  # choose a path of interest!
    source path/to/new/psychopyenv/bin/activate

Once you have a compatible Python activated, **copy the link to a wxPython wheel** for
your platform from:

https://extras.wxpython.org/wxPython4/extras/linux/gtk3/

and having downloaded the right wheel you can then install it with something like:

.. code-block:: bash

  pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/wxPython-4.2.1-cp310-cp310-linux_x86_64.whl

``wxPython>=4.0`` doesn't have universal wheels yet which is why you have to
find and install the correct wheel for your particular flavor of linux.
If a wheel is not yet available for your platform (e.g., a new version of Linux),
you will have to build it manually. For example, you can use ``pip download wxPython``,
extract the archive, enter the directory, and try ``python setup.py bdist_wheel`` to
build a wheel yourself. You will likely need to install some system build dependencies.
Once it builds, you can install for example with ``pip install dist/wxPython*.whl``.

For some reasons wxPython (wx.html2) is using an older version of libwebkitgtk
e.g. psychopy will not show up
to fix this (of our own risk):
sudo add-apt-repository 'deb http://archive.ubuntu.com/ubuntu bionic main universe'
sudo apt install -t bionic libwebkitgtk-1.0-0

Finally, you can do:

.. code-block:: bash

    # with --no-deps flag if you want to install dependencies manually
    pip install psychopy

**Building Python PsychToolbox bindings:**

The PsychToolbox bindings for Python provide superior timing for sounds and
keyboard responses. Unfortunately we haven't been able to build universal wheels
for these yet so you may have to build the pkg yourself. That should not be hard.
You need the necessary dev libraries installed first:

.. code-block:: bash

    sudo apt-get install libusb-1.0-0-dev portaudio19-dev libasound2-dev

and then you should be able to install using pip and it will build the extensions
as needed:

.. code-block:: bash

    pip install psychtoolbox


.. _conda:

Anaconda and Miniconda
~~~~~~~~~~~~~~~~~~~~~~

Support for conda was contributed and is badly outdated but you may be able to
get it working using `pip install` within your conda environment.

Generally we recommend you use StandalonePsychoPy instead, for experiment creation,
as an entirely separate app, and use your conda installation for other (e.g. analysis)
scripts.

Alternatively if someone wants to jump in and get things working here again that
would be appreciated by other users I'm sure.

.. _developers_install:

Developers install
~~~~~~~~~~~~~~~~~~~~~~

Ensure you have Python 3.8 and the latest version of pip installed::

  python --version
  pip --version

Next, follow the :ref:`instructions to fork and fetch <usingRepos>` the latest version of the |PsychoPy| repository.

From the directory where you cloned the latest |PsychoPy| repository (i.e., where setup.py resides), run::

  pip install -e .

This will install all |PsychoPy| dependencies to your default Python distribution (which should be Python 3.8). Next, you should create a new |PsychoPy| shortcut linking your newly installed dependencies to your current version of |PsychoPy| in the cloned repository. To do this, simply create a new .BAT file containing::

"C:\PATH_TO_PYTHON3.8\python.exe C:\PATH_TO_CLONED_PSYCHOPY_REPO\psychopy\app\psychopyApp.py"

Alternatively, you can run the psychopyApp.py from the command line::

  python C:\PATH_TO_CLONED_PSYCHOPY_REPO\psychopy\app\psychopyApp

.. _hardware:

Recommended hardware
-------------------------------------------------

The minimum requirement for |PsychoPy| is a computer with a graphics card that
supports OpenGL. Many newer graphics cards will work well. Ideally the graphics
card should support OpenGL version 2.0 or higher. Certain visual functions run
much faster if OpenGL 2.0 is available, and some require it (e.g. ElementArrayStim).

If you already have a computer, you can install |PsychoPy| and the Configuration
Wizard will auto-detect the card and drivers, and provide more information. It
is inexpensive to upgrade most desktop computers to an adequate graphics card.
High-end graphics cards can be very expensive but are only needed for very
intensive use.

Generally NVIDIA and ATI (AMD) graphics chips have higher performance than
Intel graphics chips so try and get one of those instead.

Notes on OpenGL drivers
~~~~~~~~~~~~~~~~~~~~~~~~

On Windows, if you get an error saying
**"pyglet.gl.ContextException: Unable to share contexts"** then the most likely
cause is that you need OpenGL drivers and your built-in Windows only has limited
support for OpenGL (or possibly you have an Intel graphics card that isn't very
good). Try installing new drivers for your graphics card **from its
manufacturer's web page,** not from Microsoft. For example, `NVIDIA provides
drivers for its cards here <https://www.nvidia.com/Download/index.aspx>`_
