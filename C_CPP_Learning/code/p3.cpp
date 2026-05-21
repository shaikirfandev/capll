#include <iostream>

using namespace std;

void call(){
    cout << "call function" << endl;
}

int addItems(int a, int b){
    call();
    return a+b;
}


int main(){
    int a = 5;
    int b = 10;
    cout << addItems(a,b) << endl;
}