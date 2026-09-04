@echo off
REM Launches the pipeline scheduler as a persistent background process.
REM Windows Task Scheduler should call THIS file (not python.exe directly) --
REM see global CLAUDE.md "Windows Task Scheduler gotchas" for why (Store
REM Python's AppExecution alias path is fragile across updates).
REM
REM Task Scheduler action settings:
REM   Program/script:    C:\Users\jjcho\code\jobs\scripts\run_scheduler.bat
REM   Start in:          C:\Users\jjcho\code\jobs
REM (these two are easy to swap in the GUI -- see CLAUDE.md gotcha #1)
REM
REM This process is meant to stay running (APScheduler's own CronTrigger
REM fires jobs at RUN_HOUR:RUN_MINUTE in scheduler.py, currently 3:30am) --
REM Task Scheduler's job here is just to make sure it's alive, e.g. via a
REM LogonTrigger + SessionStateChangeTrigger(StateChange=SessionUnlock), with
REM MultipleInstancesPolicy=StopExisting so a stale suspended instance
REM doesn't block a fresh one after sleep/wake, and ExecutionTimeLimit=PT0S
REM (no time limit) since this is a daemon, not a bounded job.

cd /d C:\Users\jjcho\code\jobs
set PYTHONPATH=src
".venv\Scripts\python.exe" -m pipeline.scheduler
