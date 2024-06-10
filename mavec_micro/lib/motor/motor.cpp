#include <Arduino.h>
#include "motor.h"

Motor::Motor(int pwmPin, int dirPin)
{
    this->pwmPin = pwmPin;
    this->dirPin = dirPin;
    pinMode(pwmPin, OUTPUT);
    pinMode(dirPin, OUTPUT);
}

Motor::~Motor()
{
}

void Motor::setSpeed(int speed, int dir)
{
    analogWrite(pwmPin, speed);
    digitalWrite(dirPin, dir);
}