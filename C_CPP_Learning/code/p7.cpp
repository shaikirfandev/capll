#include <iostream>
using namespace std;

int main(){
    cout << "Exception handling in C++" << endl;
    int age = 20;
    try{
        if(age < 21){
            cout << " exception for age: " << age << endl;
            throw runtime_error("Age must be at least 18 to vote.");
        }
        
    }
    catch(const runtime_error& e){
        cout << "Exception caught: " << e.what() << endl;
    }
    return 0;
}