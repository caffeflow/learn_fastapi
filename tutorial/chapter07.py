#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__Jack__'

from fastapi import BackgroundTasks
from pydantic import HttpUrl
import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from datetime import datetime
from datetime import date as date_
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
"""
SQLAlchemy是Python编程语言下的一款ORM框架，该框架建立在数据库API之上，使用关系对象映射进行数据库操作。
    简言之便是：将对象对应具体的数据库表，将对象的操作转换成SQL，然后使用数据API执行SQL并获取执行结果。

https://www.osgeo.cn/sqlalchemy/

在fastapi中，对于用户级别的api设计,可以让pydantic的BaseModel实例来包装一个或多个ORM框架的对象中的全部或部分属性。
"""

"""
1. 建立ORM对象关系模型的初始化
在项目结构中,下面代码可放在database.py
"""
# Connecting
database_py_engine = create_engine(
    # 数据库url格式:'数据库类型+数据库驱动名称://用户名:口令@机器地址:端口号/数据库名'
    'sqlite:///./tutorial/chapter07.sqlite3',
    encoding='utf-8', echo=True, connect_args={'check_same_thread': False}
)

# Declare a Mapping
database_py_Base = declarative_base(bind=database_py_engine, name='Base')

# Creating a Session
database_py_session = sessionmaker(
    bind=database_py_engine, autoflush=False, autocommit=False, expire_on_commit=True)

"""
2. 建立ORM
在项目结构总，下面代码可放在models.py中。

关于from sqlalchemy import Column：
    name: 数据库中表示的此列的名称。此参数可以是第一个位置参数，也可以通过关键字指定。当省略时自动赋值为python的变量名。
    type_ : 列的字段类型。该参数可以是第二个位置参数，也可以由关键字指定。
    *args -- 其他位置参数包括 SchemaItem 将作为列的选项应用的派生构造。其中包括 Constraint ， ForeignKey ， ColumnDefault ， Sequence ， Computed Identity .
    **kwargs -- 关键字参数
    参考https://www.osgeo.cn/sqlalchemy/core/metadata.html?highlight=column#sqlalchemy.schema.Column

"""


class models_py_Province(database_py_Base):
    __tablename__ = "province"  # 表名
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_name = Column(String(100), unique=True,
                           nullable=False, comment="省/直辖市")
    country_name = Column(String(100), nullable=False, comment="国家")
    country_code = Column(String(100), nullable=False, comment="国家代码")
    country_population = Column(BigInteger, nullable=False, comment="国家人口")
    # server_default:生成表结构时就被赋值的默认值 (default参数是当未赋值时的默认值)
    created_at = Column(DateTime, server_default=func.now(), comment="创建日期")
    update_at = Column(DateTime, server_default=func.now(), comment="更新日期")

    # relationship字段，其配合外键一起使用,实现表关联,可分为正向查询和反向查询，它比直接用外键查询更高效。
    # NOTE: data是关系，而不是字段。'Data'是关联的类名；back_populates来指定反向访问的属性名称
    data = relationship(argument='models_py_Data', back_populates='province')
    # todo __mapper_args__ = {}

    def __repr__(self) -> str:
        return f"<国家代码:{self.country_code} 省/直辖市:{self.province_name}>"


class models_py_Data(database_py_Base):
    __tablename__ = "data"
    # Column的name参数是数据库表的字段名,它被省略则自动赋值为python变量名
    id = Column(Integer, primary_key=True, autoincrement=True)
    # ForeignKey里的字符串格式不是类名.属性名，而是表名.字段名
    province_id = Column(Integer, ForeignKey('province.id'), comment="所属省/直辖市")
    date = Column(Date, nullable=False, comment="数据日期")
    confirm_num = Column(BigInteger, nullable=False, comment="确诊数")
    death_num = Column(BigInteger, nullable=False, comment="死亡数")
    cure_num = Column(BigInteger, nullable=False, comment="治愈数")
    created_at = Column(DateTime, server_default=func.now(), comment="创建日期")
    update_at = Column(DateTime, server_default=func.now(), comment="更新日期")
    # 'Province'是关联的类名；back_populates来指定反向访问的属性名称
    province = relationship(
        argument='models_py_Province', back_populates='data')

    def __repr__(self) -> str:
        return f"<确诊数:{self.confirm_num} 治愈数:{self.cure_num} 死亡数:{self.death_num}>"


"""
3. 建立pandatic.BaseModel数据模型

在项目结构中,下面代码放在schemas.py中
"""


class schemas_py_Create_Province(BaseModel):
    # 下面是需要手动赋值的属性
    province_name: str
    country_name: str
    country_code: str
    country_population: int


class schemas_py_Read_Province(schemas_py_Create_Province):
    # 下面是自动赋值或需要特别赋值的属性。(见对象关系模型类的属性细节)
    id: int
    created_at: datetime
    update_at: datetime

    class Config:
        # https://pydantic-docs.helpmanual.io/usage/model_config/
        orm_mode = True  # whether to allow usage of ORM mode


class schemas_py_Create_Data(BaseModel):
    date: date_
    confirm_num: int
    death_num: int
    cure_num: int


class schemas_py_Read_Data(schemas_py_Create_Data):
    id: int
    province_id: int
    created_at: datetime
    update_at: datetime

    class Config:
        orm_mode = True


"""
4. orm数据库接口
在项目结构中，可以写在crud.py
"""


def crud_py_create_province(db: Session, province: schemas_py_Create_Province):
    "创建province表"
    province_model = models_py_Province(**province.dict())  # 赋值化对象关系模型
    db.add(province_model)  # 对表的add操作添加到事务
    # flush操作告知数据库把事务操作缓存在数据库,直到数据库收到了Commit操作之后才会真正将操作更新到磁盘中
    # commit会默认调用flush，并提交当前事务,这标志事务执行完毕。
    db.commit()  # 提交缓存的事务
    db.refresh(province_model)  # 刷新数据表到对象关系模型的映射
    return province_model  # 返回对象关系模型


def crud_py_get_province(db: Session, province_id: int):
    "在province表中,取回province id对应的数据项"
    return db.query(models_py_Province).filter(models_py_Province.id == province_id).first()


def crud_py_get_province_by_name(db: Session, province_name):
    "在province表中,取回province named对应的数据项"
    return db.query(models_py_Province).filter(models_py_Province.province_name == province_name).first()


def crud_py_get_provinces(db: Session, offset: int, limit: int):
    "在province表中,取回一部分城市的数据项"
    return db.query(models_py_Province).offset(offset).limit(limit).all()
    # return db.query(models_py_Province).order_by(models_py_Province.country_code).offset(offset).limit(limit).all()


def crud_py_create_province_data(db: Session, data: schemas_py_Create_Data, province_id: int):
    "创建疫情数据表"
    data_model = models_py_Data(**data.dict(), province_id=province_id)
    db.add(data_model)
    db.commit()
    db.refresh(data_model)
    return data_model


def crud_py_get_data(db: Session, province_name: str = None, offset: int = 0, limit: int = 10):
    "在疫情数据表中,取回province name对应的所有数据项 或 最新的一堆数据项 "
    data = db.query(models_py_Data)
    if province_name is not None:
        data = data.filter(models_py_Data.province.has(
            province_name=province_name)).all()
    else:
        data = data.offset(offset).limit(limit).all()
    return data


"""
5. 业务逻辑和接口(并使用前端)  （多应用的目录结构设计:将covid19作为子应用）
在项目结构中,可以写在main.py中
"""


async def get_user_agent(request: Request):
    print(request.headers["User-Agent"])


app07 = APIRouter(
    prefix="/appstore",  # /appstore的子路径可以安排给子应用，如"/appstore/covid19/"用于covid19项目。
    dependencies=[Depends(get_user_agent)],  # 子应用的全局依赖
    responses={200: {"description": "Good job!"}},
)

# app07 = APIRouter()  # 接口路由
database_py_Base.metadata.create_all(bind=database_py_engine)  # 生成数据库和表
templates = Jinja2Templates(
    directory='tutorial/templates')  # 渲染模版


def get_db():
    db = database_py_session()
    try:
        yield db  # NOTE 这里不是异步
    finally:  # NOTE 这里不是except:
        db.close()


@app07.post('/covid19/create_province', response_model=schemas_py_Read_Province)
async def create_province(schema_create_province: schemas_py_Create_Province, db: Session = Depends(get_db)):
    # 首先判断province是否已存在
    province_db = crud_py_get_province_by_name(
        db, schema_create_province.province_name)
    if province_db:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="province already exist！")
    return crud_py_create_province(db, schema_create_province)


@app07.get('/covid19/get_province/{province_name}', response_model=schemas_py_Read_Province)
async def get_province(province_name: str, db: Session = Depends(get_db)):
    province_model = crud_py_get_province_by_name(db, province_name)
    if province_model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="province not found！")
    return province_model


@app07.get('/covid19/get_provinces', response_model=schemas_py_Read_Province)
async def get_provinces(offset: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    provinces = crud_py_get_provinces(db, offset, limit)
    return provinces


@app07.post('/covid19/create_data', response_model=schemas_py_Read_Data)
async def create_data(schema_create_data: schemas_py_Create_Data, province_name: str, db: Session = Depends(get_db)):
    # 找到province_id
    province_model = crud_py_get_province_by_name(db, province_name)
    if province_model is None:
        raise HTTPException(status_code=404, detail="未找到该province，请先创建它")
    province_id = province_model.id
    data = crud_py_create_province_data(db, schema_create_data, province_id)
    return data


@app07.get('/covid19/get_data')
async def get_data(province_name: str = None, offset: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    data = crud_py_get_data(db, province_name, offset, limit)
    return data


@app07.get("/covid19/", description="covid19应用的首页")  # 前后端不分离
def covid19(request: Request, province_name: str = None, offset: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    data = crud_py_get_data(db, province_name, offset, limit)
    return templates.TemplateResponse(
        name="home.html",  # html文件
        context={"request": request,
                 "data": data,
                 # 点击之后传递一个接口地址的常量（该接口用于同步数据）
                 "sync_data_url": "/chapter07/appstore/covid19/sync_coronavirus_data/jhu",
                 },
    )


def bg_task(url: HttpUrl, db: Session):
    """这里注意一个坑，不要在后台任务的参数中db: Session = Depends(get_db)这样导入依赖"""

    province_data = requests.get(
        url=f"{url}?source=jhu&country_code=CN&timelines=false")

    if 200 == province_data.status_code:
        db.query(models_py_Province).delete()  # 同步数据前先清空原有的数据
        for location in province_data.json()["locations"]:
            province_schema = {
                "province_name": location["province"],
                "country_name": location["country"],
                "country_code": "CN",
                "country_population": location["country_population"]
            }
            crud_py_create_province(
                db, province=schemas_py_Create_Province(**province_schema))
    coronavirus_data = requests.get(
        url=f"{url}?source=jhu&country_code=CN&timelines=true")

    if 200 == coronavirus_data.status_code:
        db.query(models_py_Data).delete()
        for province in coronavirus_data.json()["locations"]:
            province_model = crud_py_get_province_by_name(
                db, province_name=province["province"])
            for date, confirmed in province["timelines"]["confirmed"]["timeline"].items():
                data = {
                    # 把'2020-12-31T00:00:00Z' 变成 ‘2020-12-31’
                    "date": date.split("T")[0],
                    "confirme_num": confirmed,
                    "death_num": province["timelines"]["deaths"]["timeline"][date],
                    "cure_num": 0  # 每个城市每天有多少人痊愈，这种数据没有
                }
                # 这个city_id是city表中的主键ID，不是coronavirus_data数据里的ID
                crud_py_create_province_data(db, schemas_py_Create_Data(
                    **data), province_id=province_model.id)


@app07.get("/covid19/sync_coronavirus_data/jhu")
def sync_coronavirus_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """从Johns Hopkins University同步COVID-19数据"""
    background_tasks.add_task(
        bg_task, "https://coronavirus-tracker-api.herokuapp.com/v2/locations", db)
    return {"message": "正在后台同步数据..."}


"""
6. 将该子应用添加到主应用中运行
在项目结构中，可以写在run.py中。

代码省略,可见run.py
"""
