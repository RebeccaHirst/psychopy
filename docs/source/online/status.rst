.. _onlineStatus:
.. role:: darkred
.. role:: darkgreen
.. role:: darkorange

Status of online options
--------------------------

The table below shows you the current state of play of PsychoJS. Per feature we list whether it's:

1. :darkgreen:`Built-in` Supported via the PsychoPy Builder
2. :darkorange:`Prototype` Supported via tutorials or customized experiments that can be cloned and adapted. Kudos to our users for pushing the envelope!
3. :darkred:`Not supported` Supported by PsychoPy, but not yet supported by PsychoJS

.. csv-table::
  :header: "Feature","Status","Notes"
  :align: left
  :widths: 15,15,70
  :escape: \

  **Stimuli**,,
    :ref:`Dots (RDK) <dotscomponent>`, :darkorange:`Prototype`, The dots component isn't yet in PsychoJS. You could use pre-created movies instead- or try `a workaround with code components here <https://pavlovia.org/Francesco_Cabiddu/staircaserdk>`__ thanks to Francesco Cabiddu
    :ref:`Images <imagecomponent>`, :darkgreen:`Built-in`, Ensure to use the image extension when referencing images in your experiment e.g. ".png" ".jpg" - this will help avoid "Unknown Resource" errors
    :ref:`Movies <moviecomponent>`, :darkgreen:`Built-in`, Do check :ref:`mediaFormats`
    :ref:`Polygons <polygoncomponent>`, :darkgreen:`Built-in`, If using circles online use a "regular" polygon with 100 vertices - rather than using the dropdown "circle" option
    :ref:`Text <textcomponent>`, :darkgreen:`Built-in`, We recommend using "Text" rather than "TextBox" for static text online - since TextBox is still in beta
    :ref:`Textbox <textboxcomponent>`, :darkgreen:`Built-in`, For versions preceding 2022.1 textbox needed a code component with `textbox.refresh()` in the "Begin Routine" to be used on several trials
    :ref:`Grating <gratingcomponent>`, :darkgreen:`Built-in`, 
    , :darkred:`Not supported`, Apertures\, Envelope Gratings\, Noise\, Panoramic
  **Responses**,,
    :ref:`Form <formcomponent>`, :darkgreen:`Built-in`,
    :ref:`Pavlovia Surveys <pavloviasurveyroutine>`, :darkgreen:`Built-in`,
    Gyroscope, :darkorange:`Prototype`, Measures the orientation of tablets and smartphones. `Try it out <https://pavlovia.org/tpronk/demo_gyroscope>`__
    Eye-tracking, :darkorange:`Prototype`, `Try it out  <https://pavlovia.org/demos/demo_eye_tracking2/>`__
    :ref:`Keyboard <keyboardcomponent>`, :darkgreen:`Built-in`, 
    :ref:`Mouse <mousecomponent>`, :darkgreen:`Built-in`, Mouse components translate to touch responses on touch screens
    :ref:`Slider <slidercomponent>`, :darkgreen:`Built-in`, Use slider and not "rating" for online studies
    :ref:`TextBox <textboxcomponent>`, :darkgreen:`Built-in`, see above
    :ref:`Brush <brushcomponent>`, :darkgreen:`Built-in`,
    :ref:`Microphone <microphonecomponent>`, :darkgreen:`Built-in`, available in 2021.2 onward
    , :darkred:`Not supported`, Joystick\, Button boxes (Cedrus & IO Labs)\, Button component
  **Data**,,
    :ref:`CSV files <outputs>`, :darkgreen:`Built-in`, These can easily be imported into analysis software\, such as Matlab\, R\, JAMOVI\, or JASP
    :ref:`Log files <outputs>`, :darkgreen:`Built-in`, Low-level logs. These offer detailed information\, but are hard to analyze
    :ref:`MongoDB <onlineFetchingYourData>`, :darkgreen:`Built-in`, Similar to CSV\, but stored in a database instead of files
    , :darkred:`Not supported`, XLSX
  **Flow and Logic**,,
    :ref:`Code <codecomponent>`, :darkgreen:`Built-in`, Insert snippets of programming code\, which can be automatically translated from Python to JavaScript
    :ref:`Loops <loops>`, :darkgreen:`Built-in`, Loops allow randomization and importing condition files.
    :ref:`Staircases <loops>`, :darkorange:`Prototype`, Adapt aspects of a trial based on earlier responses of a participant. You can use Multistair but specify only a single staircase - see below. Or try out a "Just Noticeable Difference" staircase via  `staircase-demo <https://pavlovia.org/demos/staircase-demo/>`__
    :ref:`Multistair <loops>`, :darkgreen:`Built-in`, Interleave several basic staircases. 
    :ref:`QUEST staircases <loops>`, :darkgreen:`Built-in`, This is currently supported via `jsQUEST <https://github.com/kurokida/jsQUEST>`__ you can `try a demo <https://run.pavlovia.org/tpronk/demo_jsquest/>`__ and access the `gitlab project <https://gitlab.pavlovia.org/tpronk/demo_jsquest>`__ to build on for your own research
  **External Tools**,,
    AMT, :darkgreen:`Built-in`, Amazon Mechanical Turk. See instructions in this `forum post <https://discourse.psychopy.org/t/how-to-use-mturk-for-recruiting/8486/7>`__
    Prolific, :darkgreen:`Built-in`, See instructions at :ref:`Recruiting with Prolific <prolificIntegration>`
    Qualtrics, :darkgreen:`Built-in`, There are many guides available for integrating Qualtrics on our `forum <https://discourse.psychopy.org/search?q=qualtrics>`__
    Sona, :darkgreen:`Built-in`, See instructions at the `Sona Systems website <https://www.sona-systems.com/help/psychopy.aspx>`__

*Thanks go out to Anastasia Carter, Arnon Weinberg, Francesco Cabiddu, Lindsay Santacroce, and Wakefield Carter; they made tutorials and/or demo experiments available that we referenced in the list above.*

Anything else we should add to the list above? Built a cool prototype? Please tell us via the `PsychoPy Forum <https://discourse.psychopy.org/c/online/14>`__.
