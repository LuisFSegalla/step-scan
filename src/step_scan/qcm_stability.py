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
        #############################################
    except KeyError as e:
        _logger.error(f"key error while reading from config file\n{e}")
        return
    motorRBV = motorPV + ".RBV"
    motorDMOV = motorPV + ".DMOV"
    motorTWV = motorPV + ".TWV"
    motorTWF = motorPV + ".TWF"

    # PCOMP block
    pandaPcompEnable = pandaPV + ":PCOMP1:ENABLE"
    pandaPcompStart = pandaPV + ":PCOMP1:START"
    pandaPcompStep = pandaPV + ":PCOMP1:STEP"
    pandaPcompPulses = pandaPV + ":PCOMP1:PULSES"

    # Pulse Block
    pandaPulsePulses = pandaPV + ":PULSE1:PULSES"
    pandaPulseWidth = pandaPV + ":PULSE1:WIDTH"

    # PCAP Block
    pandaPCAPEnable = pandaPV + ":PCAP:ENABLE"
    pandaPcapArm = pandaPV + ":PCAP:ARM"
    # Data Blocks
    pandaDataDirectory = pandaPV + ":DATA:HDF_DIRECTORY"
    pandaDataFilename = pandaPV + ":DATA:HDF_FILE_NAME"
    pandaDataCapture = pandaPV + ":DATA:CAPTURE"

    numSteps = int(abs(stopPos - startPos) / step)
    caput(motorTWV, step)

    print(
        f"Sending motor to initial position @ ({startPos})"
    )
    # Move motor to start position caput
    try:
        caput(motorPV, startPos - step, wait=True, timeout=100)
    except:
        print("timeout while trying to move to initial position.\n\
              Manualy move the motors to initial position and run the scan again.")

    print(f"Motor reached initial position @ ({startPos})")

    # Configure the PandA to receive data
    ctxt.put(pandaDataDirectory, filepath)
    ctxt.put(pandaDataFilename, filename)

    # Configure PCOMP
    ctxt.put(pandaPcompStart, int(startPos / mres))
    ctxt.put(pandaPcompStep, int(abs(step / mres)) - 50)
    ctxt.put(pandaPcompPulses, numSteps)

    # Configure Pulse
    ctxt.put(pandaPulsePulses, triggersPerStep)
    ctxt.put(pandaPulseWidth, triggerWidth)

    ctxt.put(pandaPcompEnable, "ONE")
    ctxt.put(pandaPCAPEnable, "ONE")
    ctxt.put(pandaDataCapture, 1)
    ctxt.put(pandaPcapArm, 1)

    currentPos = caget(motorRBV)

    # Add some time to wait while the PandA is acquiring position data.
    sleepPerStep = triggersPerStep * 1e-3 * 2
    print(f"sleeping for {sleepPerStep}s each step")
    while currentPos <= (stopPos + step):
        try:
            caput(motorTWF, 1)
            dmov = caget(motorDMOV)
            while not dmov:
                Sleep(1)
                dmov = caget(motorDMOV)

            Sleep(sleepPerStep)
            currentPos = caget(motorRBV)
        except:
            print("Problem while running the scan")
            break
    ctxt.put(pandaPcompEnable, "ZERO")
    ctxt.put(pandaPCAPEnable, "ZERO")
    ctxt.put(pandaDataCapture, 0)
    ctxt.put(pandaPcapArm, 0)
    print("finished the program")
