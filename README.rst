Here's how I generate the scala code::

    python generate-scala-code.py crash_report.json

Or from a remote url (requires ``requests``)::

    python generate-scala-code.py https://github.com/mozilla/socorro/raw/master/socorro/schemas/crash_report.json

To generate Python code (instead of Scala) add::

    --python
