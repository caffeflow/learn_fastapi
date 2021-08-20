#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__Jack__'

from fastapi import APIRouter, Depends, Request

"""【见coronavirus应用】SQL (Relational) Databases FastAPI的数据库操作"""

"""Bigger Applications - Multiple Files 多应用的目录结构设计"""


async def get_user_agent(request: Request):
    print(request.headers["User-Agent"])


app07 = APIRouter(
    prefix="/biger",
    dependencies=[Depends(get_user_agent)],  # 子应用的全局依赖
    responses={200: {"description": "Good job!"}},
)


@app07.get("/bigger_applications")
async def bigger_applications():
    return {"message": "Bigger Applications - Multiple Files"}
