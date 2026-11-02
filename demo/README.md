# Browser demo with fictional data

[Open the demo](https://bib007.github.io/LTM-Local-Territory-Manager/) at the root URL, including the trailing `/`. No installation or account is required.

The static demo stores fictional records in this browser only. Choose the fictional administrator or assignment assistant to explore their available screens and actions. These are demonstrations of permissions, not secure accounts: the installed server enforces its own roles. Do not enter real information. The demo cannot import private records or connect to your installation or Google Drive.

English is the default for new visitors; Danish and a choice of appearance are available. Existing language preferences are retained. Some content is still partially translated.

Build the demo with `python3 scripts/build_demo.py`. The checked-in design snapshot is updated with `python3 scripts/sync_demo_design.py`. Hosting is optional and separate from installation; see [demo hosting](../docs/DEMO-HOSTING.md). Server code, databases and private keys are not included in the public demo.
