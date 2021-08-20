from fastapi import FastAPI
from coronavirus import application
from tutorial import app03, app04, app05, app06, app07  # , app08
import uvicorn
from fastapi.staticfiles import StaticFiles

# 异常处理类
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import HTTPException


app = FastAPI(title="tutorial", description="基本知识", docs_url='/docs')

# mount表示将某个目录下一个完全独立的应用挂载过来，这个不会在API交互文档中显示
app.mount(path='/static', app=StaticFiles(directory='./coronavirus/static'),
          name='static')  # .mount()不要在分路由APIRouter().mount()调用，模板会报错


# 1-导入接口路由，将子应用添加到主应用
app.include_router(app03, prefix='/chapter03', tags=['第三章 请求参数和验证'])
app.include_router(app04, prefix='/chapter04', tags=['第四章 响应处理和FastAPI配置'])
app.include_router(app05, prefix='/chapter05', tags=['第五章 FastAPI的依赖注入系统'])
app.include_router(app06, prefix='/chapter06', tags=['第六章 安全、认证和授权'])
app.include_router(app07, prefix='/chapter07',
                   tags=['第七章 数据库操作和多应用的目录结构设计（结合covid-19项目）'])

# app.include_router(app08, prefix='/chapter08', tags=['第八章 中间件、CORS、后台任务、测试用例'])


# @app.exception_handler(HTTPException)  # 重写HTTPException异常处理器
# async def http_exception_handler(request, exc):  # 函数名不是固定的
#     """
#     :param request: 这个参数不能省
#     :param exc:
#     :return:
#     """
#     return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

#
#
# @app.exception_handler(RequestValidationError)  # 重写请求验证异常处理器
# async def validation_exception_handler(request, exc):
#     """
#     :param request: 这个参数不能省
#     :param exc:
#     :return:
#     """
#     return PlainTextResponse(str(exc), status_code=400)


if __name__ == '__main__':
    uvicorn.run('run_:app', host='0.0.0.0', port=8000,
                reload=True, debug=True, workers=1)
