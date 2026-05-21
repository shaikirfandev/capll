#include <iostream>
#include <vector>

using namespace std;


int main(){
	std::vector<int> v;
	v.push_back(4);
	v.push_back(1);
	v.push_back(2);
	v.push_back(1);
	v.push_back(4);

	for(int i : v){
		cout << "Elements " << i << endl;
	}
	cout << "Finding the unique element in the vector" << endl;
	int result = 0;
	for(int i : v){
		result ^= i;
	}
	cout << "The unique element is " << result << endl;	

	

	return 0;
}