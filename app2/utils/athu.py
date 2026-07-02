from jose import jwt,JWTError
from datetime import datetime,timedelta
from passlib.context import CryptContext

SECRET_KEY="secret"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10
REFRESH_TOKEN_EXPIRE_DAYS=7


# to create access token and refresh token
def create_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

def access_token(token:str):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        return payload
    except JWTError:
        return None

def refresh_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow() +timedelta(hours=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp":expire})
    encode_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encode_jwt

# hashing and verifying passwords

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str):
    return pwd_context.hash(password[:72])

def verify_password(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

# reset password token generation and verification

def create_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=15)
    data = {
        "sub": email,
        "exp": expire
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None