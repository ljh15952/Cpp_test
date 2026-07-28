const string& GetNameBad() {
	string local = "test";
	return local; // Returning reference to local variable (bad)
}

const string GetName() {
	string local = "test";
	return local;
}

int main() {
	cout << GetName() << endl; // Safe: returns a copy of the string
	cout << GetNameBad() << endl; // Undefined behavior: accessing a dangling reference
	return 0;
}
