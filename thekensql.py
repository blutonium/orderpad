import mysql.connector
import base64
import json
import os

product_table = 'products'
product_key = 'product_id'
product_rows_to_fetch = ['product_id', 'name', 'liter', 'min_age']
order_table = 'orders'


class ThekenSQL:
    def __init__(self, id):
        self.db = None
        self.host:str = ''
        self.user:str = ''
        self.passwd:str = ''
        self.database:str = ''
        self.midi_client = id

    def save(self, file):
        with open(file, "w") as f:
            data = str(self.passwd)
            encodedBytes = base64.b64encode(data.encode("utf-8"))
            passwd = str(encodedBytes, "utf-8")

            d = {
                'host': str(self.host),
                'user': str(self.user),
                'passwd': passwd,
                'database': str(self.database)
            }
            f.write(json.dumps(d, indent=2))

    def connected(self):
        return self.db and self.db.is_connected()    

    def load(self, file):
        if os.path.exists(file):
            with open(file, "r") as f:
                d = dict(json.loads(f.read()))
                if d:
                    if 'host' in d:
                        self.host = d['host']
                    if 'user' in d:
                        self.user = d['user']
                    if 'passwd' in d:
                        self.passwd = base64.b64decode(d['passwd'])
                    if 'database' in d:
                        self.database = d['database']             
                    return True
        return False
    
    def connect(self):
        if not self.connected():
            try:
                self.db = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    passwd=self.passwd,
                    database=self.database
                    )            
                if self.db and self.db.is_connected():
                    db_Info = self.db.get_server_info()
                    print("Connected to MySQL Server version", db_Info)
                    cursor = self.db.cursor()
                    try:
                        cursor.execute("select database();")
                        record = cursor.fetchone()
                        if len(record) > 0:
                            print("Connected to database:", record[0])  
                        return True
                    finally:
                        cursor.close()                                  
            except Exception as e:
                print("Error while connecting to MySQL", e)
            
        return False

    def fetchProducts(self):
        if self.connected():            
            cursor = self.db.cursor()
            try:
                cursor.execute("select " + ','.join(product_rows_to_fetch) + " from " + product_table)
                records = cursor.fetchall()
                print('Fetched', cursor.rowcount, 'Products!')

                products = {}        
                for row in records:        
                    d = {}
                    for idx, column in enumerate(product_rows_to_fetch):
                        d[column] = row[idx]

                    products[d[product_key]] = d

                return products 
            except Exception as e:
                print("Error while fetching products", e)
            finally:
                cursor.close()
                
        else:
            print('Failed to fetch products: SQL is not connected.')
            return None

    def addOrder(self, product_id):
        if self.connected():            
            cursor = self.db.cursor()
            try:
                sql = "INSERT INTO " + order_table + "(product_id, midi_client) VALUES (" + str(product_id) + "," + str(self.midi_client) + ")"
                cursor.execute(sql)

                self.db.commit()

                print(cursor.rowcount, "record inserted.")
            except Exception as e:
                print("Error while fetching products", e)
            finally:
                cursor.close()

        else:
            print('Failed to add order: SQL is not connected')
        
  
if __name__ == "__main__":
    sql = ThekenSQL(1)    
    if not sql.load('sql.json'):
        sql.host = input('SQL Hostname: ')
        sql.user = input('SQL Username: ')
        sql.passwd = input('SQL Password: ')
        sql.database = input('SQL Database: ')
        sql.save('sql.json')

    if sql.connect():
        print('SQL connected')
        print(sql.fetchProducts())
        #sql.addOrder(1)