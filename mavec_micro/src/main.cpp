#include <Arduino.h>

#include <motor.h>
#include <Servo.h>

#include "config.h"

void readData();

int partNum = 0;
int angle = 90;
int speed = 0;
byte read_angle = 0;
byte read_speed = 0;

Motor motor(MOTORA, MOTORB);
Servo servo;

void setup()
{
  Serial.begin(57600);
  servo.attach(SERVO_PIN);
}

void loop()
{
  readData();
  servo.write(angle);
  motor.setSpeed(speed);
}

void readData()
{
  if (Serial.available() > 0)
  {                                    // Check if data is available to read
    byte receivedChar = Serial.read(); // Read the incoming byte
    switch (partNum)
    {
    case 0:
      if (receivedChar == 'A')
        partNum++;
      else
      {
        partNum = 0;
      }
      break;
    case 1:
      read_angle = receivedChar;
      partNum++;
      break;
    case 2:
      read_speed = receivedChar;
      partNum++;
      break;
    case 3:
      if (receivedChar == 'B')
      {
        partNum = 0;
        angle = read_angle;
        speed = read_speed;

        // Serial.print("Success angle:");
        // Serial.print(angle);
        // Serial.print(", speed:");
        // Serial.print(speed);
        // Serial.print('\n');
      }
      else
      {
        partNum = 0;
        // Serial.print("Error\n");
      }

    default:
      break;
    }
  }
}