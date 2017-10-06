from subprocess import Popen
from time import sleep

if __name__ == '__main__':
    # Main control loop for handling process launch, restarting failed servers...

    # 1. Activate the oracle.
    oracle_app = Popen(['python', 'oracle.py'])

    # Start the Kivy application.
    kivy_app = Popen(['python', 'biomonitor.py'])

    # Monitor processes. Shut down on keyboard break.
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print('Shutting down all processes...')
        oracle_app.kill()
        kivy_app.kill()

