#!/bin/bash

# Use venv
source venv/bin/activate

# Init database
(python init_db.py)
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to download statics from Golemio. EXIT $status" >&2
  exit $status
fi

# Start background worker
(celery -A pid-tasks worker)&
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start celery worker. EXIT $status" >&2
  exit $status
fi

# Start celery beats
(celery -A pid-tasks beat -s ./instance/celerybeat-schedule)&
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start celery beat. EXIT $status" >&2
  exit $status
fi


# Naive check runs checks once a minute to see if either of the processes exited.
# This illustrates part of the heavy lifting you need to do if you want to run
# more than one service in a container. The container exits with an error
# if it detects that either of the processes has exited.
# Otherwise it loops forever, waking up every 60 seconds

while sleep 60; do
  ps aux | grep celery | grep -q -v grep
  PROCESS_2_STATUS=$?
  # If the greps above find anything, they exit with 0 status
  # If they are not both 0, then something is wrong
  if [ $PROCESS_2_STATUS -ne 0 ]; then
    echo "Celery has already exited." >&2
    exit 1
  fi
done