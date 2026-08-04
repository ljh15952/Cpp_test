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
