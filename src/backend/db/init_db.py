import sqlite3


DB_PATH = "exchange_rates.db"


connection = sqlite3.connect(DB_PATH, check_same_thread=False)

connection.row_factory = sqlite3.Row

connection.execute('PRAGMA journal_mode=WAL;')  
connection.execute('PRAGMA synchronous=NORMAL;')  
connection.execute('PRAGMA foreign_keys = ON;')


class DatabaseInitializer:
    def __init__(self, conn = connection):
        self.conn = conn

    def create_tables(self):
        try:
            with self.conn as conn:
                cursor = conn.cursor()
                

                cursor.execute("PRAGMA foreign_keys = ON;")


                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Currencies (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Code VARCHAR NOT NULL,
                        FullName VARCHAR NOT NULL,
                        Sign VARCHAR NOT NULL
                    )
                ''')


                cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_currencies_code 
                    ON Currencies (Code)
                ''')


                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ExchangeRates (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        BaseCurrencyId INTEGER NOT NULL,
                        TargetCurrencyId INTEGER NOT NULL,
                        Rate DECIMAL(10, 6) NOT NULL,
                        FOREIGN KEY (BaseCurrencyId) REFERENCES Currencies (ID),
                        FOREIGN KEY (TargetCurrencyId) REFERENCES Currencies (ID),
                        UNIQUE (BaseCurrencyId, TargetCurrencyId) -- Чтобы не было дублей одной пары
                    )
                ''')

                conn.commit()
                print("База данных успешно инициализирована.")
                
        except sqlite3.Error as e:
            print(f"Ошибка при инициализации базы данных: {e}")