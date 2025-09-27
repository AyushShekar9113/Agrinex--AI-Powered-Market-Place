from pymongo import MongoClient

# MongoDB Atlas connection URI (replace this with your actual URI)
client = MongoClient("mongodb+srv://agrinex_db_bhairava:Agrinex@cluster0.d4oijiu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['agrinex']
admin_collection = db['admin']

# Admin details
username = "ASG"
email = "admin@agrinex.com"
plain_password = "supadmin123"
role = "superadmin"

# Generate unique admin_id by combining role and username
admin_id = f"{role}_{username}"

# Insert admin with plain text password
admin_collection.insert_one({
    "username": username,
    "email": email,
    "password": plain_password,  # Plain text password
    "role": role,
    "admin_id": admin_id  
})

print(f"✅ Admin '{username}' created successfully.")
