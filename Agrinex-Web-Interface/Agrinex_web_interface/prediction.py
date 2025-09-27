# 


print("Starting script")

from pymongo import MongoClient
import certifi

print("Connecting to MongoDB...")

uri = "mongodb+srv://agrinex_db_bhairava:Agrinex@cluster0.d4oijiu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, tlsCAFile=certifi.where())
print("Connected. Listing databases:")
print(client.list_database_names())
