
# HttpRunner
## 设计理念

- 约定优于配置
- 投资回报率问题
- 拥抱开源， [`requests`], [`pytest`], [`pydantic`], [`allure`] 和 [`locust`].

## 主要特点

- 继承 的所有强大功能 [`requests`][requests]，享受以人性化方式处理 HTTP(S) 的乐趣。
- 以 YAML 或 JSON 格式定义测试用例， [`pytest`][pytest] 以简洁优雅的方式运行。
- 在 [`HAR`][HAR] 支持下记录和生成测试用例。
- 支持 `variables`/`extract`/`validate`/`hooks` 机制，以创建非常复杂的测试方案。
- 使用 `debugtalk.py` 插件，任何函数都可以用于测试用例的任何部分。
- 使用 [`jmespath`][jmespath], 提取和验证 json 响应从未如此简单。
- 使用 [`pytest`][pytest], 可以轻松获得数百个插件。
- 使用 [`allure`][allure], 测试报告可以非常漂亮和强大。
- 通过重用 [`locust`][locust], 您无需额外工作即可运行性能测试。
- 支持 CLI 命令，与 `CI/CD`.



## HttpRunner依赖库

> 出自: https://github.com/httprunner/httprunner/blob/master/pyproject.toml
> HttpRunner 使用了 `poetry`库 来进行包管理 和打包的操作

```shell
requests = "^2.22.0"    # 请求库
pyyaml = "^5.1.2"     # 解析yaml
jinja2 = "^2.10.3"    # 模板文件，生产测试文件
pydantic = "^1.4"     # 数据类型定义，类型校验
loguru = "^0.4.1"     # 日志
jmespath = "^0.9.5"   # json 提取
black = "^19.10b0"    # python 代码格式化工具
pytest = "^5.4.2"     # 单元测试框架
pytest-html = "^2.1.1"  # 简易html报告
sentry-sdk = "^0.14.4"  # 捕捉异常
allure-pytest = "^2.8.16" # allure 报告
requests-toolbelt = "^0.9.1"  # 估计是上传文件用到的
filetype = "^1.0.7"   # 文件类型判断
locust = "^1.0.3"     # 协程实现的性能测试工具 [此次学习不带它]
Brotli = "^1.0.9"   # 压缩
```

## 1. 体验

```shell
# 安装
pip install httprunner

# 创建项目
httprunner startproject demo

# 运行项目
hrun demo
```

[![f9UiiF.gif](https://z3.ax1x.com/2021/08/02/f9UiiF.gif)](https://imgtu.com/i/f9UiiF)

### 最终目录结构

![img](https://gitee.com/zy7y/blog_images/raw/master/img/20210802162647.png)

## 该系列要阅读的内容

![img](https://gitee.com/zy7y/blog_images/raw/master/img/20210802162949.png)

## httprunner目录结构分析

```shell
│  cli.py       # 命令封装
│  client.py    # request封装，网络请求client
│  compat.py    # 用例适配，处理testcase格式v2和v3之间的兼容性问题。
│  exceptions.py  # 自定义异常
│  loader.py    # 加载用例设计文件JSON/YAML、环境变量、参数化，生成model定义的测试数据
│  make.py      # 依据测试数据生产pytest测试文件，并格式化生成的python代码
│  models.py    # pydantic 数据模型定义
│  parser.py    # 参数解析器，解析用例当中引用变量、自定义方法等
│  response.py  # 响应内容处理：断言、变量提取
│  runner.py    # 执行/启动器
│  scaffold.py  # HttpRunner 脚手架，快速生成httprunner测试项目
│  testcase.py  # 测试用例对象封装
│  utils.py     # 工具类
│  __init__.py  # 初始化文件，指定httprunner库包含的模块
│  __main__.py  # httprunner命令入库，调用cli.py的main函数
│
├─app     # 网络服务模块
│  │  main.py
│  │  __init__.py
│  │
│  └─routers
│     │  debug.py
│     │  debugtalk.py
│     │  deps.py
│     └─__init__.py
│ 
├─builtin # 内置方法、校验比较器，供YAML/JSON用例设计文件中testcases使用
│  │  comparators.py
│  │  functions.py
│  └─__init__.py
│
└─ext # 扩展功能
   │  __init__.py
   │
   ├─har2case     # har 文件 转 httprunner测试用例文件
   │  │  core.py
   │  │  utils.py
   │  └─__init__.py
   │          
   ├─locust      # 性能测试相关
   │  │  locustfile.py
   │  └─__init__.py
   │
   └─uploader  # 文件上传
      │  
      └─__init__.py
```