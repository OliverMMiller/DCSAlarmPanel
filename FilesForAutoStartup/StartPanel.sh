#!/bin/bash
echo "StartPanel script running at $(date)" >> /home/donfigol/DCSAlarmPanel/ServiceLog.log
cd /home/donfigol/DCSAlarmPanel/
/home/donfigol/DCSAlarmPanel/env/bin/python InstructorStation.py >> ServiceLog.log 2>&1
#/home/donfigol/DCSAlarmPanel/env/bin/python HelmStation.py >> ServiceLog.log 2>&1