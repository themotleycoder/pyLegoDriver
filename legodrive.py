import thread
from nxt.motor import *
from nxt.sensor import *
import nxt.locator

brick = nxt.locator.find_one_brick(name="MainBot")
motora = nxt.Motor(brick, nxt.PORT_A)
motorb = nxt.Motor(brick, nxt.PORT_B)
motorc = nxt.Motor(brick, nxt.PORT_C)
touch = nxt.Touch(brick, PORT_1)

wheels = [motorb, motorc]

def runmotor(motor, power, degrees, brake=False):
	motor.turn(power, degrees, False, 3, False)

def runwheels(power, degrees=1, brake=False):
	for motor in wheels:
		motor.run(power=power)

def stopwheels(power=0, degrees=1, brake=False):
	for motor in wheels:
		motor.idle()		

def runmotorthread(motor, power, degrees, brake=False):
	thread.start_new_thread(
		runmotor,
		(motor, power, degrees, brake))

def touch():
	return touch.get_sample()