libck2
**********************************************

A C++ code library for easily and efficiently accessing low- and high-level
information in the game files of `Crusader Kings II`_, a product of `Paradox Development Studios`_.

.. _`Crusader Kings II`: https://en.wikipedia.org/wiki/Crusader_Kings_II
.. _`Paradox Development Studios`: https://en.wikipedia.org/wiki/Paradox_Development_Studio

Past, Present & Future
----------------------

The current incarnation of the library is actually a resumption of what was
thought to be an end-of-life fork of my eldest hand-written parser for CKII
game files. In its current state, I would caution against its usage, and the
[realistic for remnants of a long-running codebase] logjam of competing styles
and standards of its code. When the API has stabilized, ``libck2`` will move
to its own repository and begin semantic versioning.

Instead of let it rot, I'm returning to the library after a great deal of time
to add a big hunk of functionality which has otherwise been spread across
multiple projects, updating all of it to C++17, and improving the API. I also
have aims to rewrite its lexical analyzer and parser for much greater
flexibility, which will also allow for additional although likely minimal,
unified support for the other publicly released and actively developed games
from `Paradox Development Studios`_ (PDX_):

- `Europa Universalis IV`_
- `Hearts of Iron IV`_
- `Stellaris`_

.. _`Europa Universalis IV`: https://en.wikipedia.org/wiki/Europa_Universalis_IV
.. _`Hearts of Iron IV`: https://en.wikipedia.org/wiki/Hearts_of_Iron_IV
.. _`Stellaris`: https://en.wikipedia.org/wiki/Stellaris_(video_game)
.. _`PDX`: https://en.wikipedia.org/wiki/Paradox_Development_Studio

If expansion of game support does indeed actually happen, this library will be
renamed ``libpdx``.

If possible, I also intend to provide a dual C API which shall then further
provide Python bindings to at least the library's core parsing engine, making
a very high speed and robust such engine for these game files available to
virtually anyone that can program. In my CK2 modding team (HIP_)'s experience
over the past several years, this task does indeed need acceleration and
careful memory management for any ambitious scripting task driven by Python.

.. _`HIP`: http://hip.zijistark.com/

In the end, the goal is to finally wrap up this library as a first-class
programming tool for people scripting and/or modding these games. It should
not only be a read-only API into these games' files, but it should also
support rewriting when possible/reasonable (and with a minimal diff when
possible as well).
