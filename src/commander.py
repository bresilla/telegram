import subprocess
import os
import time
import signal

def run_external_command(command):
    process = subprocess.Popen(command, shell=True)
    return process.pid

def kill_process(pid):
    try:
        os.kill(pid, signal.SIGTERM)
    except:
        print(f"Coudn't kill process: {pid}")

def main():
    command_to_run = "/pkg/mamba/envs/pytorch/bin/python /doc/code/telegram/src/main.py"
    timeout_seconds = 600  # 10 minutes
    try:
        while True:
            pid = run_external_command(command_to_run)
            print(f"External command started with PID: {pid}")
            time.sleep(timeout_seconds)
            kill_process(pid)
            print(f"External command with PID {pid} terminated.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()