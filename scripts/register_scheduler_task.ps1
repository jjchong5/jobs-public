# Registers the JobsPipelineScheduler Windows Task Scheduler entry.
# Run this in an ELEVATED (Run as Administrator) PowerShell window --
# Register-ScheduledTask needs admin rights this repo's sandboxed shell
# doesn't have.
#
# Fires scripts/run_scheduler.bat on logon and on session-unlock (per
# global CLAUDE.md's Task Scheduler gotchas: sleep/wake doesn't kill the
# process, so a SessionUnlock trigger is needed to get a fresh one after
# wake). MultipleInstancesPolicy=StopExisting so a stale suspended instance
# doesn't block a fresh one; ExecutionTimeLimit=PT0S (unlimited) since this
# is a long-running daemon, not a bounded job.

$taskName = 'JobsPipelineScheduler'
$batPath = 'C:\Users\jjcho\code\jobs\scripts\run_scheduler.bat'
$workDir = 'C:\Users\jjcho\code\jobs'

$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $workDir
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn

$class = Get-CimClass -ClassName MSFT_TaskSessionStateChangeTrigger -Namespace root/Microsoft/Windows/TaskScheduler
$unlockTrigger = New-CimInstance -CimClass $class -ClientOnly
$unlockTrigger.StateChange = 2  # TASK_SESSION_UNLOCK

$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan) -DontStopOnIdleEnd -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

$task = Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($logonTrigger, $unlockTrigger) -Settings $settings -Principal $principal -Description 'Runs pipeline.scheduler (nightly job-source ingest/tag/rank at 3:30am) as a persistent process, restarted on logon/unlock.'

# Register-ScheduledTask's cmdlet enum doesn't expose StopExisting by name
# (only Parallel/Queue/IgnoreNew) -- patch the underlying XML definition
# directly via the COM Task Scheduler API instead.
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()
$folder = $svc.GetFolder('\')
$def = $folder.GetTask($taskName).Definition
$def.Settings.MultipleInstances = 2  # 2 = TASK_INSTANCES_STOP_EXISTING
$folder.RegisterTaskDefinition($taskName, $def, 6, $null, $null, 3) | Out-Null  # 6 = TASK_CREATE_OR_UPDATE, 3 = TASK_LOGON_INTERACTIVE_TOKEN

Write-Host "Registered '$taskName'. Verify with: Get-ScheduledTask -TaskName '$taskName' | Format-List"
