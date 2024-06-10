#pragma once

class Motor
{
private:
public:
    int pwmPin;
    int dirPin;
    Motor(int pwmPin, int dirPin);
    ~Motor();
    void setSpeed(int, int);
};
