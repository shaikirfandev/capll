#include <iostream>

using namespace std;

void check(int x){
	int temp;
	int sum = 0;
	while(x > 0){
      temp = x % 10;
      sum = sum+temp;
      x = x / 10;
	}
	return sum
}

int main(){
	int var = 1450;
	cout << "sum of the digits of number" << check(var);
}