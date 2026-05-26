#include<iostream>
#include<vector>

using namespace std;


int main(){
    float pamount,time,intrest;
    float totalAmount;
    cout << "Please enter amount and time and inrest to calculate amount " << endl;
    while (pamount && time && intrest){
    	cin >> pamount;
    	cout << endl;
    	cin >> time;
    	cout << endl;
    	cin >> intrest;

    	totalAmount = (pamount*time*intrest) / 100;

    	cout << "Total simple itrest calculated " << totalAmount;

    }

    return 0;
}