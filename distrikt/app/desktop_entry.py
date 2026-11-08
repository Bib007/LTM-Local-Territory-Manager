"""Self-contained desktop entry, without system Python or private cloud services."""
import runpy
import sys

import server
import s13_reader  # Ensure separate PDF reader is included by PyInstaller.


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ['--ltm-read-s13']:
        # Maintain the existing disposable subprocess boundary for PDF imports.
        runpy.run_module('s13_reader', run_name='__main__')
        return
    server.main(args)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('LTM kunne ikke starte: ' + str(error), file=sys.stderr)
        sys.exit(1)
