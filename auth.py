"""
In this file we define a set of functions that will later be used in the main project.
Below I will explain their intended purpose.

I will not delve too deep into how "hashing" and "salting" actually works or what it even is. I will just asssume you already know.
If you don't know, ask me in person. I will explain.
"""

#We import the bcrypt library since we intend to use its hashing methods.
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Cookie, HTTPException
from typing import Optional

#Well... the string explains it.
SECRET_KEY = "change-this-in-production"

#The SECRET_KEY variable is passed to the URLSafeTimedSerializer function 
# to cryptographically sign the session data before it is delivered.

#The only problem is that if a malicious actor (like me) were to get a hold of the SECRET_KEY,
# they could just craft their own valid sessions and login as any user (would be (really) bad in real production).

serializer = URLSafeTimedSerializer(SECRET_KEY)


#This function is quite honest. It takes the user's password as plaintext
# and passes it to the hashpw() method to hash the poassword before it's stored in the databse.
#It will be used when it's time to create a new user profile.
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

#This one will be used to verify the input of the user when they try to log into their profile.
#It takes the input of the user and matches it with the hashed password stored in the databse. We use the checkpw() method for this.
#The way I would assume it works is by first hashing the attempted input and compare it to the existing hashed password in the databse.
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

#This functions does what it says.
#It works by taking the user's unique ID stored in the database and uses (itsdangerous) serializer to package and sign it cryptographically.
#This is mainly for safety altough most of these checks are useless once you think remember that this will run locally on your machine.
def create_session(user_id: int) -> str:
    return serializer.dumps(user_id)

#This one is a little bit more interesting. I might need to comment multiple parts of it.
#The intended purpose is simple. It makes sure that in order to acess the user profile, you must have a valid cookie/session.
def get_current_user(session: Optional[str] = Cookie(default=None)) -> int:
    #We make the check here. If the user doesn't have a session, the server raises an HTTP exception and redirects them back to the login page.
    if session is None:
        raise HTTPException(status_code=307, headers={"Location": "/login"})
    #If the cookie is present though, it will try to unpack the user id with the secret key.
    #But if it notices that the cookie was modified or that it is older than 86400 seconds (24 hours)
    # it will reject the attempt and send you back to the login page anyway.
    try:
        user_id: int = serializer.loads(session, max_age=86400)
        return user_id
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=307, headers={"Location": "/login"})