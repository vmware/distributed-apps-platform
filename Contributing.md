Contributing
============

Contributions are welcome in the form of bug reports or pull requests.

Bug Reports
-----------
Quality bug reports are welcome at the [Distributed Apps Platform](https://github.com/vmware/distributed-apps-platform/issues).

There are plenty of [good resources](http://www.drmaciver.com/2013/09/how-to-submit-a-decent-bug-report/) describing how to create
good bug reports. They will not be repeated in detail here, but in general, the bug report include where appropriate:

* relevant software versions (Python version, endpoints egg version, runner egg version)
* details for how to produce (e.g. a test script or written procedure)
  * any effort to isolate the issue in reproduction is much-appreciated
* stack trace from a crashed runtime

Pull Requests
-------------
If you're able to fix a bug yourself, you can [fork the repository](https://help.github.com/articles/fork-a-repo/) and submit a [Pull Request](https://help.github.com/articles/using-pull-requests/) with the fix.
Please include tests demonstrating the issue and fix. To ensure the changes are not breaking existing tests, makes sure to run existing tests by running this [script](https://github.com/vmware/distributed-apps-platform/blob/master/LYDIAN/run_tests.sh).

Contribution License Agreement
------------------------------
Please check license agreement in the root folder of the project.

Design and Implementation Guidelines
------------------------------------
- Avoid 3rd party module dependencies as much as possible. It is intended to keep this platform as lightweight as possible.
- Avoid adding deendencies on modules which have been added lately (e.g. six) . Project is intended to be supported on as old release as possible.
- Consider fault tolerance as necessity when writing your app. If a newly introduced app fails for a reason, it shouldn't bring the whole platform down.

