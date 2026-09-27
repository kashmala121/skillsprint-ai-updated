"""
Run once after connecting to MongoDB Atlas to create the first admin login:
    cd backend
    python -m app.seed_admin
"""
import asyncio
from app.database import users_col
from app.auth import hash_password


async def main():
    existing = await users_col.find_one({"username": "admin"})
    if existing:
        print("Admin user already exists.")
        return
    await users_col.insert_one({
        "username": "admin",
        "password_hash": hash_password("Admin@123"),
        "role": "admin",
        "full_name": "System Administrator",
    })
    print("Created admin user -> username: admin / password: Admin@123 (change this after first login)")


if __name__ == "__main__":
    asyncio.run(main())
