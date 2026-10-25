echo "StartHornButton script running at $(date)"
cd /home/donfigol/DCSAlarmPanel/
source env/bin/activate
python3 /home/donfigol/DCSAlarmPanel/InstructorPanel.py >> /home/donfigol/DCSAlarmPanel/ServiceLog.log 2>&1
#python3 /home/donfigol/DCSAlarmPanel/HelmStation.py >> /home/donfigol/DCSAlarmPanel/ServiceLog.log 2>&1
