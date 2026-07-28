#include "Player.h"
#include <iostream>
#include <vector>

using namespace std;

int main() {
	// 1. 객체를 직접 저장
	vector<Player> objects;

	Player player;
	player.setHealth(10);
	objects.push_back(player);

	player.setHealth(20);
	objects.push_back(player);

	// Player 객체의 복사본을 수정
	for (auto p : objects) {
		p.setHealth(p.getHealth() + 100);
	}

	cout << "A: ";
	for (auto& p : objects) {
		cout << p.getHealth() << " ";
	}
	cout << '\n';

	// Player 객체 자체를 참조하여 수정
	for (auto& p : objects) {
		p.setHealth(p.getHealth() + 10);
	}

	cout << "B: ";
	for (auto& p : objects) {
		cout << p.getHealth() << " ";
	}
	cout << '\n';

	// 2. 포인터를 저장
	vector<Player*> pointers;

	for (int i = 0; i < 2; ++i) {
		Player* p = new Player();
		p->setHealth(i + 1);
		pointers.push_back(p);
	}

	// 포인터는 복사되지만 같은 객체를 수정
	for (auto p : pointers) {
		p->setHealth(p->getHealth() + 10);
	}

	std::cout << "C: ";
	for (auto p : pointers) {
		std::cout << p->getHealth() << " ";
	}
	std::cout << '\n';

	// 복사된 포인터만 nullptr로 변경
	for (auto p : pointers) {
		p = nullptr;
	}

	std::cout << "D: "
		<< (pointers[0] == nullptr ? "nullptr" : "not nullptr")
		<< '\n';

	// 벡터 내부 포인터 자체를 nullptr로 변경
	// 먼저 객체를 삭제하여 메모리 누수를 방지
	for (auto& p : pointers) {
		delete p;
		p = nullptr;
	}

	std::cout << "E: "
		<< (pointers[0] == nullptr ? "nullptr" : "not nullptr")
		<< '\n';

	return 0;
}
