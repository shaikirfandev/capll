#include <iostream>
#include <vector>

using namespace std;


int main(){
	int num = 10;
	std::vector<int> v;
    for(int i = 0;i<num;i++){
    	v.push_back(i);
    }
    for(int i : v){
    	cout << "items in vector" << i << endl;
    }
    cout << endl;
	return 0;
}