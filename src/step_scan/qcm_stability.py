"""My module for running step scans with the PandA."""

import json
import logging

from cothread import Sleep
from cothread.catools import caget, caput
from p4p.client.thread import Context

ctxt = Context("pva")


def run_scan(configpath: str = ""):
    """Method for running the step scan.

    This will open a configuration file provided by the user
    and use it's information to configure the scan.
    """
    _logger = logging.Logger("log")
    try:
        f = open(configpath)
        options = json.loads(f.read())
    except OSError as e:
        _logger.error(f"Could not open the file!\n{e}")
        return

    try:
        #############################################
        # USER CONFIG
        motorPV = options["motorPV"]  # CA
        pandaPV = options["pandaPV"]  # PVA

        # Motor config
        startPos = options["startPos"]
        stopPos = options["stopPos"]
        step = options["step"]
        mres = options["mres"]

        # Panda config
        filepath = options["filepath"]
        filename = options["filename"] + ".h5"
        triggersPerStep = options["triggersPerStep"]
        triggerWidth = options["triggerWidth"]
        loops = options["loops"]
        #############################################
    except KeyError as e:
        _logger.error(f"key error while reading from config file\n{e}")
        return

    motorRBV = motorPV + ".RBV"
    motorDMOV = motorPV + ".DMOV"
    motorTWV = motorPV + ".TWV"
    motorTWF = motorPV + ".TWF"
    motorTWR = motorPV + ".TWR"

    # Pulse Block
    pandaPulsePulses = pandaPV + ":PULSE1:PULSES"
    pandaPulseWidth = pandaPV + ":PULSE1:WIDTH"
    pandaPulseTrig = pandaPV + ":PULSE1:TRIG"

    # PCAP Block
    pandaPCAPEnable = pandaPV + ":PCAP:ENABLE"
    pandaPcapArm = pandaPV + ":PCAP:ARM"
    # Data Blocks
    pandaDataDirectory = pandaPV + ":DATA:HDF_DIRECTORY"
    pandaDataFilename = pandaPV + ":DATA:HDF_FILE_NAME"
    pandaDataCapture = pandaPV + ":DATA:CAPTURE"

    # Configure the PandA to receive data
    ctxt.put(pandaDataDirectory, filepath)
    ctxt.put(pandaDataFilename, filename)

    # Configure Pulse
    ctxt.put(pandaPulsePulses, triggersPerStep)
    ctxt.put(pandaPulseWidth, triggerWidth)

    ctxt.put(pandaPCAPEnable, "ONE")
    ctxt.put(pandaDataCapture, 1)
    ctxt.put(pandaPcapArm, 1)

    # Add some time to wait while the PandA is acquiring position data.
    sleepPerStep = triggersPerStep * 1e-3 * 2

    # Initial stop condition
    stop = stopPos + step if startPos < stopPos else stopPos - step
    start = startPos - step if startPos < stopPos else startPos + step

    caput(motorTWV, step)

    print(f"sleeping for {sleepPerStep}s each step")
    for _ in range(loops):
        print(f"Going from {start} to {stop}")
        print(
            f"Sending motor to initial position @ ({start})"
        )

        # Move motor to start position caput
        try:
            caput(motorPV, start, wait=True, timeout=100)
        except:
            print("timeout while trying to move to initial position.")

        print(f"Motor reached initial position @ ({start})")

        currentPos = caget(motorRBV)

        # Change which PV we're using based on the direction we're going with the motor
        motorTW = motorTWF if start < stop else motorTWR
        if start < stop:
            while currentPos <= stop - step:
                try:
                    caput(motorTW, 1)
                    dmov = caget(motorDMOV)
                    while not dmov:
                        Sleep(1)
                        dmov = caget(motorDMOV)

                    ctxt.put(pandaPulseTrig, "ONE")
                    Sleep(sleepPerStep)
                    currentPos = caget(motorRBV)
                    ctxt.put(pandaPulseTrig, "ZERO")
                except:
                    print("Problem while running the scan")
                    break
        else:
            while currentPos >= stop - step:
                try:
                    caput(motorTW, 1)
                    dmov = caget(motorDMOV)
                    while not dmov:
                        Sleep(1)
                        dmov = caget(motorDMOV)

                    ctxt.put(pandaPulseTrig, "ONE")
                    Sleep(sleepPerStep)
                    currentPos = caget(motorRBV)
                    ctxt.put(pandaPulseTrig, "ZERO")
                except:
                    print("Problem while running the scan")
                    break
        tmp = stop
        stop = start
        start = tmp

    ctxt.put(pandaPCAPEnable, "ZERO")
    ctxt.put(pandaDataCapture, 0)
    ctxt.put(pandaPcapArm, 0)
    print("finished the program")
