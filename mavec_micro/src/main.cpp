#include <Arduino.h>

int part_num = 0;
int angle = 0;
int speed = 0;

void setup()
{
  Serial.begin(57600);
}

void loop()
{
  if (Serial.available() > 0)
  {                                    // Check if data is available to read
    char receivedChar = Serial.read(); // Read the incoming byte
    switch (part_num)
    {
    case 0:
      if (receivedChar == 'A')
        part_num++;
      else
      {
        part_num = 0;
      }
      break;
    case 1:
      angle = receivedChar;
      part_num++;
      break;
    case 2:
      speed = receivedChar;
      part_num++;
      break;
    case 3:
      if (receivedChar == 'B')
      {
        part_num = 0;
        Serial.print("Success angle:");
        Serial.print(angle);
        Serial.print(", speed:");
        Serial.print(speed);
        Serial.print('\n');
      }
      else
      {
        part_num = 0;
        Serial.print("Error\n");
      }

    default:
      break;
    }
  }
}
