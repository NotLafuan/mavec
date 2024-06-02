#pragma once

class Motor
{
private:
public:
    int leftPin;
    int rightPin;
    Motor(int leftPin, int rightPin);
    ~Motor();
    void setSpeed(int);
};
