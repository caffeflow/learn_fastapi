# learn_fastapi

learn fastapi。implemente some api


```
1. 了解 FastAPI 框架特性，相对 Django/Flask 的优势
2. Pydantic 定义和规范数据格式、类型
3. 如何定义各种请求参数和验证，包括路径参数、查询参数、请求体、cookie、header
4. Jinja2 模板渲染和 Static 静态文件配置
5. FastAPI 的表单数据处理、错误处理、响应模型、文件处理、路径操作配置等
6. 全面学习 FastAPI 的依赖注入系统
7. FastAPI 的安全、认证和授权，OAuth2 认证和 JWT 认证的实现
8. FastAPI 的数据库配置与 SQLAlchemy ORM 的使用
9. 大型工程应该如何目录结构设计，多应用的文件拆分
10. FastAPI 的中间件开发
11. FastAPI 中跨域资源共享 CORS 的原理和实现方式
12. 如何编写后台任何和测试用例"
```


```
    导入 FastAPI。
    创建一个 app 实例。
    编写一个路径操作装饰器（如 @app.get("/")）。
    编写一个路径操作函数（如上面的 def root(): ...）。
    运行开发服务器（如 uvicorn main:app --reload）。

启动服务：\
    uvicorn main:app --reload [--port 8000]
文档:\
    1.http://127.0.0.1:8000/docs
    2.http://127.0.0.1:8000/redoc
    3.http://127.0.0.1:8000/openapi.json
```



```
补充笔记

http:
    OST：创建数据。
    GET：读取数据。
    PUT：更新数据。
    DELETE：删除数据。

http协议的简要过程:
    (其他参考：https://www.cnblogs.com/ranyonsue/p/5984001.html)
    客户端想dns服务器查询域名对应的ip地址，
    客户端通过”ip地址+提供服务的相对url“来发送http请求给服务器，服务器返回响应，
        如返回html，其中html内部可能还有多媒体等url，这些都交给客户端再次请求服务器,
            由于url地址可能发生变换，所以整个页面可能是由多个服务器共同提供的，
                客户端在拿到响应之后，会进行渲染，最终可视化给用户。
http请求构成：
    1.请求行 GET /hello.txt HTTP/1.1 
    2.请求头 Host: www.example.com 
    3.空行
    4.请求数据 ...
    ... 
http响应构成:
    1.状态行 HTTP/1.1 200 OK
    2.消息报头 Content-Type: text/plain #文件编码
    3.空行
    3.响应正文 <html> ... </html> 

rest api 规范:
    1. 编写res api 就是编写处理http请求的async函数，但是特殊在普通的http请求:\
        rest仍然是标准http请求，但是请求的Content-Type的属性值和响应的Content-Type的属性值均为application/json,\
            即请求和响应均为json数据格式 （注：get请求除外）
        - 个人感悟：json数据 <-> async函数的参数与返回。

    3.例如,商品product就是一种资源:\
        1.获取所有product的url： GET /api/products
        2.获取指定product的url,例如id=123： GET /api/products/123
        3.新建一个product使用post请求，json数据包含在body中: POST /api/products
        3.更新指定product使用put请求,例如id=123: PUT /api/products/123
        4.删除指定product使用delete请求,例如id=123： DELETE /api/products/123
        5.资源可以按层次组织,例如指定product的所有评论: GET /api/products/123/reviews
        6.通过参数限制返回的结果集，以获取部分数据。例如，返回第二页评论，每页10项，按时间排序：\
            GET /api/products/123/reviews?page=2&size=10&sort=time


    4. 开发rest api:\
        1.如何组织url\
            web应用既有rest,还有mvc，可能还集成其他第三方系统，如何组织url呢？\
                1. 简单办法：通过固定的前缀区分。例如,/static/开头的url是静态资源文件,\
                    类似地，/api/开头url是rest api，其他url是普通mvc请求。
        2.如何统一输出rest：\
            每个异步函数都编写下面这样的代码。\
                // 设置content-type:
                ctx.response.type= 'application/json';
                // 设置response body:
                ctx.respose.body = {
                    products: products
                };

        3.如何处理错误:\
            ...
     
```