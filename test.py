from sense_hat import SenseHat

sense = SenseHat()

while True:
	acceleration = sense.get_accelerometer_raw()
	x = acceleration['x']
	y = acceleration['y']
	z = acceleration['z']

	print(f"x={x:6.3f}, y={y:6.3f}, z={z:6.3f}")