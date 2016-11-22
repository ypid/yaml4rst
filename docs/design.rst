Design principles
-----------------

.. include:: /includes/all.rst

* Idempotent.

  The program can be run against it’s output and should not make any changes to
  it. This property is checked by integration testing.

  This allows users to integrate the program into their workflow and let
  :program:`yaml4rst` do the repetitive tasks.

* Keep it simple.

  The Python implementation is thought to be close to the way a human would solve the problem.
  It basically just parses each line of input into fold sections and checks if
  something needs to be changed. At the end, the sections are formated back to
  lines and written to the output.

* Committed to excellence.

  This program is reasonably small and it’s scope can be clearly defined so
  that it is possible even for one person to try to follow most of the best
  practices in Python programming which includes:

  * Extensive unit and integration testing
  * 100 % unit test `code coverage <https://coverage.readthedocs.io/en/latest/index.html>`_
    (including `branch coverage <https://coverage.readthedocs.io/en/latest/branch.html>`_)
  * Python version test matrix
  * Python linting tools like :program:`pylint`
  * Documentation build testing
  * No redundancy

  Furthermore, most of the best practices listed above are automatically checked
  (where possible) on each commit and before PRs get accepted.

* Why not do it manually? Hoped to be helpful.

  "How long can you work on making a routine task more efficient before you’re
  spending more time than you save?"
  (Ref: `xkcd 1205`_)

  "I spend a lot of time on this task. I should write a program automating it!"
  (Ref: `xkcd 1205`_)

  Based on the analysis of git-hours_ it took ypid 118 hours for the initial
  public commit.
  This equals 14.75 days (assuming 8 hours a day).
  The time for ongoing maintenance of the program is not included and can be
  estimated based on the public commits.

  From that it is clear that for ypid, it took much longer to
  automate the task then it would have been to do it manually.
  But that is only part of the story because ypid is not the only person doing
  this kind of maintenance.
  So it is believed that this effort will still pay of in saving time for
  everyone doing this and lead to more productivity and higher quality.
  (Ref: Collective_)

* No formal parsing/lexing.

  Existing parsers for YAML where found to be unsuited for the use in a
  statical analyser/reformatter like this program.

  Also, ypid is more familiar with this hacky approach then he would
  like to confess (ref: opening_hours.js_).

* Don’t reimplement error checking from Ansible or RST parsers.

  The input is not extensively checked. Use Ansible and RST before and/or after
  the reformatting through this program.
