echo "StartHornButton script running at $(date)"
cd /home/donfigol/DCSAlarmPanel/
python3 /home/donfigol/DCSAlarmPanel/InstructorPanel.py >> /home/donfigol/DCSAlarmPanel/ServiceLog.log 2>&1
#python3 /home/donfigol/DCSAlarmPanel/AlarmPanel.py >> /home/donfigol/DCSAlarmPanel/ServiceLog.log 2>&1
