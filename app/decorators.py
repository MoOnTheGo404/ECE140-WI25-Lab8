from functools import wraps
from typing import Callable, Optional, Dict, Any, List, Tuple
from fastapi import Request, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse
import inspect
import mysql.connector
from mysql.connector import pooling
import secrets
import hashlib
import uuid
import time
import json
from datetime import datetime, timedelta
from pydantic import BaseModel

def auth_required(func: Callable) -> Callable:
    """
    Universal authentication decorator for FastAPI route handlers.
    Works with both sync and async functions.
    
    Usage:
    ```
    @app.get("/protected")
    @auth_required
    def protected_route(request: Request):
        return {"message": "This is a protected route"}
    
    @app.get("/protected-async")
    @auth_required
    async def protected_async_route(request: Request):
        return {"message": "This is a protected async route"}
    ```
    """
    is_async = inspect.iscoroutinefunction(func)
    
    if is_async:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract request from args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), kwargs.get('request', None))
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found in function arguments")

            # Check if user is authenticated
            session_id = request.cookies.get("sessionId")
            if not session_id:
                return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
            
            session = await get_session(session_id)
            if not session:
                return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

            # Set user in request state for later access
            user = await get_user_by_id(session["user_id"])
            request.state.user = user

            # Extend session (optional: update timestamp if needed)

            # Continue with the original function
            return await func(*args, **kwargs)
        
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract request from args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), kwargs.get('request', None))
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found in function arguments")

            # Check if user is authenticated
            session_id = request.cookies.get("sessionId")
            if not session_id:
                return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

            session = get_session(session_id)  # Assuming sync support or wrap in asyncio.run if needed
            if not session:
                return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

            # Set user in request state for later access
            user = get_user_by_id(session["user_id"])
            request.state.user = user

            # Extend session (optional: update timestamp if needed)

            # Continue with the original function
            return func(*args, **kwargs)
        
        return sync_wrapper

