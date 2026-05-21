#include <iostream>
#include <vector>
using namespace std;

int main(){
	std::vector<int> v;
	for(int i = 0;i<10;i++){
		v.push_back(i);
	}
	for(int j : v){
		cout <<"Elements in Vector " << j;
		cout << endl;
	}

	cout << "Size of Vector " << v.size() << endl;
	cout << "Capacity of Vector " << v.capacity() << endl;

	return 0;

}


