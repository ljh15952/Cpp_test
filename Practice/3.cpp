#include "Player.h"
#include <iostream>
#include <vector>

using namespace std;

int main() {
	
	vector<Player*> players;
	players.emplace_back(new Player(100));
	//vector<Player> players;
	//players.emplace_back(100);
	for (auto player : players) {
		player->hello();
		cout << "Health: " << player->getHealth() << endl;
		player->setHealth(150);
	}

	for (auto& player : players) {
		player->hello();
		cout << "Health: " << player->getHealth() << endl;
	}
	return 0;
}

#include "Player.h"
#include <iostream>
#include <vector>
#include <span>
using namespace std;


void printArr(span<int> arr) {
	for (auto& i : arr) {
		cout << i << " ";
		++i;
	}
	cout << endl;
}

int main() {
	
	int arr1[] = { 1, 2, 3, 4, 5 };
	vector<int> arr2 = { 6, 7, 8, 9, 10 };

	printArr(arr1);
	printArr(arr2);

	printArr(arr1);
	printArr(arr2);
	return 0;
}
