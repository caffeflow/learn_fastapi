#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__Jack__'

from pydantic import EmailStr
from fastapi.security import OAuth2PasswordBearer  # Bearer令牌
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext  # .hash()生成哈希,.verity()验证哈希
from pydantic import BaseModel

app06 = APIRouter()

"""
OAuth2.0的授权模式分为4类:
    授权码授权模式( Authorization code grant)
    隐式授权模式( Implicit Grant)
    密码授权模式( Resource Owner Password Credentials grant) ---> (fastapi采用)
    客户端凭证授权模式( Client credentials grant)
"""

"""
fastapi推荐使用密码授权模式的oauth2，我在下面具体实现了两种oauth2认证方式,两种区别在于使用不同的token,第一种实现更简单，第二种实现更安全。
    1.Bearer-token的OAuth2，主要模块: 
        from fastapi.security import OAuth2PasswordRequestForm - 登陆模块：客户端填写登陆表单并进行用户验证，成功则创建token作为响应体,并向指定url发送该响应体。
        from fastapi.security import OAuth2PasswordBearer - 接收URL作为参数的一个类：前有客户端向该URL发送token作为响应体，后有该模块得到这个token。
        from passlib.context import CryptContext - 用于哈希密码的生成和校验。
    2.JWT-token的OAuth2,主要模块:
        相比Bearer-token的OAuth2，额外多了from jose import JWTError, jwt - 通过jwt.encode()和jwt.decode()实现了对token的签名和有效期等等功能。
"""


"""
方式一：Bearer-token的OAuth2OAuth2认证
"""


class Gender(str, Enum):
    male = "male"
    female = "female"


def fake_hashed_password(password: str):
    "模拟生成哈希密码"
    return "fakehashed_"+password


fake_users_db = {
    # 模拟一个数据库数据
    "jia": {
        "username": "jia",
        "gender": Gender.male,
        "hashed_password": fake_hashed_password("jia_secret"),  # 数据库保存hashed密码
        "email": "jia@qq.com",
        "activate": True  # 是否活跃
    },
}


class User(BaseModel):
    # 创建一个用户基本模型
    username: str
    gender: Gender
    email: EmailStr
    activate: bool


class UserInDB(User):
    # 创建一个对应数据库中数据的用户模型
    hashed_password: str


def fake_token_encode(user: UserInDB):
    token = user.username + "_token"
    return token


def fake_token_decode(token: str):
    username = token[:-len("_token")]
    user = fake_users_db.get(username)
    if user is not None:
        return UserInDB(**user)  # 创建为Pydantic模型
    return None


@app06.post(path="/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    登陆模块：客户端填写登陆表单并进行用户验证，成功则创建token作为响应体,并向指定url发送该响应体。
    OAuth2PasswordRequestForm 是一个类依赖项，声明了如下的请求表单：
        username。
        password。
        一个可选的 scope 字段，是一个由空格分隔的字符串组成的大字符串。
        一个可选的 grant_type.
        一个可选的 client_id。
        一个可选的 client_secret。
    """
    http_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")

    # 表单验证并返回token
    username = form_data.username
    password = form_data.password
    user = fake_users_db.get(username)
    if user is None:
        raise http_exception
    user = UserInDB(**user)  # 创建为Pydantic模型
    if user.hashed_password != fake_hashed_password(password):
        raise http_exception
    token = fake_token_encode(user)
    return {"access_token": token, "token_type": "bearer"}  # 固定的响应形式


# OAuth2PasswordBearer是接收URL作为参数的一个类：前有客户端会向该URL发送token作为响应体，后有该模块得到这个token。
# 有了这个token，后续对token进行解码得到用户数据,就用于验证过程了。
# 这里token来源于依赖OAuth2PasswordRequestForm的登陆模块，所以tokenUrl务必和登陆模块的url一致(指在浏览器中的实际url)。
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/chapter06/token", scheme_name="scheme name by jia", description="desc by jia")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 嵌套依赖 # 获取当前用户
    user = fake_token_decode(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            # OAuth2的规范，如果认证失败，请求头中返回“WWW-Authenticate”
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def user_is_activate(user: UserInDB = Depends(get_current_user)):
    # 嵌套依赖 # 验证用户是否激活
    if not user.activate:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="未激活用户")
    return user


@app06.get("/users/me")
async def user_is_me(user: UserInDB = Depends(user_is_activate)):
    # 嵌套依赖 # 激活用户可进行的一系列操作
    return user


"""方式二: JWT-token的OAuth2 认证

    OAuth2 with Password (and hashing), Bearer with JWT tokens 开发基于JSON Web Tokens的认证 ：
        JWT 表示 「JSON Web Tokens」，它是一个将 JSON 对象编码为密集且没有空格的长字符串的标准。字符串看起来像这样：
            eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
        它没有被加密，因此任何人都可以从字符串内容中还原数据。
        但它经过了签名。因此，当你收到一个由你发出的令牌时，可以校验令牌是否真的由你发出。
        通过这种方式，你可以创建一个有效期为 1 周的令牌。然后当用户第二天使用令牌重新访问时，你知道该用户仍然处于登入状态。
        一周后令牌将会过期，用户将不会通过认证，必须再次登录才能获得一个新令牌。而且如果用户（或第三方）试图修改令牌以篡改过期时间，你将因为签名不匹配而能够发觉。
        如果你想上手体验 JWT 令牌并了解其工作方式，可访问 https://jwt.io。
    安装:
        pip install python-jose[cryptography]
            Python-jose 需要一个额外的加密后端，这里我们使用的是推荐的后端：pyca/cryptography。
        pip install passlib[bcrypt]
            PassLib 是一个用于处理哈希密码的很棒的 Python 包,推荐安装附带 Bcrypt算法 的 PassLib
"""

# OAuth2PasswordBearer是接收URL作为参数的一个类：前有客户端会向该URL发送token作为响应体，后有该模块得到这个token。
# 有了这个token，后续对token进行解码得到用户数据,就用于验证过程了。
# 这里token来源于依赖OAuth2PasswordRequestForm的登陆模块，所以tokenUrl务必和登陆模块的url一致(指在浏览器中的实际url)。
oauth2_scheme_jwt = OAuth2PasswordBearer(tokenUrl="/chapter06/jwt/token")
# 该模块帮助使用多种算法对密码进行哈希和验证。
secret_context = CryptContext(
    # 下面列出你希望支持的hash算法。默认是bcrypt算法，如果报错的话试一试安装pip install passlib[bcrypt]
    schemes=["bcrypt", "pbkdf2_sha256", "des_crypt"],
    # Automatically mark all but first hasher in list as deprecated.
    # (this will be the default in Passlib 2.0)
    # deprecated="auto",
)
# jwt令牌相关,是jwt.encode()和jwt.decode()的参数。
# JWT_KEY是随机密匙，用于jwt-token的签名。使用下面命令来产生:openssl rand -hex 32
# JWT_ALGORITHMS是jwt.encode和jwt.decode方法所采用的算法
# JWT_EXPIRE是给jwt.encode设置的token过期时间
JWT_KEY = "1fe4746e0133b33b4017c5878aeac7a18fb68ef3a829d596a95f562ef45c7d1d"
JWT_ALGORITHMS = jwt.ALGORITHMS.HS256
JWT_EXPIRE = 30


def gen_hashed_secret(plain_secret: str):
    return secret_context.hash(str(plain_secret))


def verify_hashed_secret(plain_secret: str, hashed_secret: str):
    return secret_context.verify(secret=plain_secret, hash=hashed_secret)


# 模拟数据库中的数据
fake_users_db_jwt = {
    "jia": {
        "username": "jia",
        "email": "jia@example.com",
        "gender": Gender.male,
        # 数据库中要保持哈希密码
        "hashed_password": gen_hashed_secret(plain_secret="jia_secret"),
        "activate": True,
    },
}


class User_jwt(BaseModel):
    username: str
    email: str
    gender: Gender
    activate: bool


class UserInDB_jwt(User_jwt):
    hashed_password: str


class Token_jwt(BaseModel):
    "token响应模型"
    access_token: str
    token_type: str


@app06.post("/jwt/token", response_model=Token_jwt)
async def login_for_access_token_jwt(data_form: OAuth2PasswordRequestForm = Depends()):
    """登陆模块：客户端填写登陆表单并进行用户验证，成功则创建jwt-token作为响应体,并向指定url发送该响应体"""
    http_exception = HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail="用户名或密码不正确",
        headers={"WWW-Authenticate": "Bearer"},
    )

    username = data_form.username
    password = data_form.password
    # 校验用户名和密码
    user = fake_users_db_jwt.get(username)
    if user is None:
        raise http_exception

    user = UserInDB_jwt(**user)  # 包装为用户数据库模型
    if not verify_hashed_secret(plain_secret=password,
                                hashed_secret=user.hashed_password):
        raise http_exception

    # 创建jwt-token
    # from jose import JWTError, jwt
    try:
        expire_time = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE)  # timedelta类型
        # token过期失效是jwt自动的,不需要去额外手动实现判断.
        access_token = jwt.encode(claims={"sub": user.username, "exp": expire_time},
                                  key=JWT_KEY,
                                  algorithm=JWT_ALGORITHMS)
    except JWTError:
        raise http_exception
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user_jwt(token: str = Depends(oauth2_scheme_jwt)):
    """
    之前依赖OAuth2PasswordRequestForm类的登陆模块返回了token响应体，
    现在，使用依赖OAuth2PasswordBearer类的验证模块进行相关验证
    """
    credentials_exception = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="找不到token或token失效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        jwt_decode = jwt.decode(token=token,
                                key=JWT_KEY,
                                algorithms=JWT_ALGORITHMS)
        username = jwt_decode.get("sub")
        if username is None:
            # 找不到token
            raise credentials_exception
    except:
        raise credentials_exception

    user = fake_users_db_jwt.get(username)
    if user is None:
        raise credentials_exception
    user = UserInDB_jwt(**user)
    return user


def get_current_activate_user_jwt(user: UserInDB_jwt = Depends(get_current_user_jwt)):
    if not user.activate:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户未激活")
    return user


@app06.get("/jwt/users/me", response_model=User_jwt)  # 这里响应不含密码的用户数据模型
def get_user_me_jwt(user: UserInDB_jwt = Depends(get_current_activate_user_jwt)):
    return user
