import sqlite3
import pytz
import datetime
import pickle


db = sqlite3.connect('DATA/accounts.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)

# SQL Tables creation (if them not exists)
db.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY NOT NULL, balance INTEGER NOT NULL)")
db.execute(
    "CREATE TABLE IF NOT EXISTS history (time TIMESTAMP NOT NULL, account TEXT NOT NULL,"
    "amount INTEGER NOT NULL, zone INTEGER NOT NULL, PRIMARY KEY (time, account))")

# Creation of new SQLite view
db.execute("CREATE VIEW IF NOT EXISTS localhistory AS"
           " SELECT strftime('%Y-%m-%d %H:%M:%f', history.time, 'localtime') AS localtime,"
           "history.account, history.amount FROM history ORDER BY history.time")


class Accounts(object):

    # Static method for downloading a date which then be put in chosen column
    @staticmethod
    def _current_time():
        utc_time = pytz.utc.localize(datetime.datetime.utcnow())
        local_time = utc_time.astimezone()
        zone = local_time.tzinfo
        return utc_time, zone

    # Constructor
    def __init__(self, name: str, initial_balance: int = 0):
        cursor = db.execute("SELECT name, balance FROM accounts WHERE (name=?)",(name,))

        row = cursor.fetchone()

        if row:
            self.name, self._balance = row #Tu zachodzi wypakowanie tuplesów
            print("Retreived record for {}".format(self.name), end="\n")
        else:
            self.name = name
            self._balance = initial_balance
            cursor.execute("INSERT INTO accounts VALUES(?,?)",(name, initial_balance)) #dodajemy nowy rekord do tabeli
            cursor.connection.commit() # w celu zapisania zmian do bazy
            print("Accounts created for {}".format(self.name), end="\n")
        self.show_balance()

    # Method which every time save the balance account after operation (withdrawal or deposit)
    def _save_update(self, amount):
        new_balance = self._balance + amount
        deposit_time, zone = Accounts._current_time() # <----- unpack returned tuple
        picked_zone = pickle.dumps(zone)

        db.execute("UPDATE accounts SET balance = ? WHERE name = ?",(new_balance, self.name ))
        db.execute("INSERT INTO history VALUES (?, ?, ?, ?)", (deposit_time, self.name, amount, picked_zone))
        db.commit()
        self._balance = new_balance

    def deposit(self, amount: int) -> float:
        if amount > 0.0:
            self._save_update(amount)
            print("{:.2f} Deposited".format(amount/100))
        return self._balance / 100

    def withdraw(self, amount: int) -> float:
        if 0 < amount <= self._balance:
            self._save_update(-amount)
            print("{:.2f} Withdrawn ".format(amount/100))
            return amount / 100
        else:
            print("Not enough money on balance account")
            return 0

    def show_balance(self):
        print("Balance on account {} is {:.2f}".format(self.name, self._balance / 100))


if __name__ == "__main__":
    Tom = Accounts("Tom")
    Tom.deposit(1010)
    Tom.deposit(10)
    Tom.deposit(10)
    Tom.withdraw(30)
    Tom.withdraw(0)
    Tom.show_balance()

    Ewa = Accounts("Ewa")
    Ewa.deposit(200)
    Ewa.show_balance()

    eric = Accounts("Eric", 7000)
    michael = Accounts("Michael")
    michael.deposit(100)
    michael.withdraw(50)
    terryG = Accounts("TerryG")

db.close()