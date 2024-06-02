#include <Arduino.h>
#include "motor.h"

Motor::Motor(int leftPin, int rightPin)
{
    this->leftPin = leftPin;
    this->rightPin = rightPin;
    pinMode(leftPin, OUTPUT);
    pinMode(rightPin, OUTPUT);
}

Motor::~Motor()
{
}

void Motor::setSpeed(int speed)
{
    if (speed > 0)
    {
        analogWrite(leftPin, speed);
        analogWrite(rightPin, 0);
    }
    else if (speed < 0)
    {
        analogWrite(leftPin, 0);
        analogWrite(rightPin, -speed);
    }
    else
    {
        analogWrite(leftPin, 0);
        analogWrite(rightPin, 0);
    }
}