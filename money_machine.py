import json


class Bank:
    def __init__(self):
        # noinspection SpellCheckingInspection
        self.path = "C:/Users/cvela/MyCodeFolder/PythonFolder/Bots/Fatbot/bank.json"
        self.users = {477249470732697601: "James", 477270012592259082: "Dylan", 387334819232874498: "Cristobal"}

    def display_balance(self, user_id):
        balances = self._load_json()
        return balances[self.users[user_id]]

    def withdraw(self, amount, user_id):
        balances = self._load_json()
        projected_balance = balances[self.users[user_id]] - amount

        if projected_balance < 0 or amount < 0:
            raise ValueError
        else:
            balances[self.users[user_id]] = projected_balance

        self._update_json(balances)

    def deposit(self, amount, user_id):
        balances = self._load_json()

        if amount < 0:
            raise ValueError
        else:
            balances[self.users[user_id]] += amount

        self._update_json(balances)

    def _load_json(self):
        with open(self.path, "r") as file:
            balances = json.load(file)

        return balances

    def _update_json(self, new_balances):
        with open(self.path, "w") as file:
            json.dump(new_balances, file, indent=4)
