"""main."""

from optparse import OptionParser

from step_scan.qcm_stability import run_scan


def main():
    """Main entrypoint."""
    parser = OptionParser()
    parser.add_option("-f",
                      "--filename",
                      action="store",
                      type="string",
                      dest="filename")
    (config, _) = parser.parse_args()
    run_scan(config.filename)


if __name__ == "__main__":
    main()
