#!/usr/bin/env python3
"""
Script to create a superuser for the MCP Tools platform.
This script uses the fastapi-users built-in functionality.
"""

import asyncio
import uuid
from database import get_async_session
from models import User
from fastapi_users.password import PasswordHelper
from sqlmodel import select


async def create_superuser():
    """Create a superuser interactively."""
    print("Creating a superuser for MCP Tools...")
    
    # Get user input
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()
    
    if not email or not password:
        print("Email and password are required!")
        return
    
    # Get database session
    async for session in get_async_session():
        try:
            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                print(f"❌ User with email {email} already exists!")
                return
            
            # Create user directly in database
            password_helper = PasswordHelper()
            hashed_password = password_helper.hash(password)
            user = User(
                id=uuid.uuid4(),
                email=email,
                hashed_password=hashed_password,
                is_superuser=True,
                is_verified=True,
                is_active=True
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"✅ Superuser created successfully!")
            print(f"   Email: {user.email}")
            print(f"   ID: {user.id}")
            print(f"   Is Superuser: {user.is_superuser}")
            
        except Exception as e:
            print(f"❌ Error creating superuser: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
        
        break


if __name__ == "__main__":
    asyncio.run(create_superuser())
