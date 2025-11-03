#include <string>
#include<Arduino.h>

#include"Time.hpp"

main(){
    std::string myString = "the string";
    String MyArduinoString = String(myString.c_str());

    return 0;
}