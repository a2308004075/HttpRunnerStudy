# 定义各种model类,以BaseModel为父类
"""
可用资料
    [pydantic]https://blog.csdn.net/codename_cys/article/details/107675748
"""
import os
from enum import Enum
from typing import Any
from typing import Dict, Text, Union, Callable  # Callable是一个可调用对象类型
from typing import List

from pydantic import BaseModel, Field
from pydantic import HttpUrl

Name = Text
Url = Text
BaseUrl = Union[HttpUrl, Text]  # 表示即可以是HttpUrl，也可以是Text
VariablesMapping = Dict[Text, Any]
FunctionsMapping = Dict[Text, Callable]
Headers = Dict[Text, Text]
Cookies = Dict[Text, Text]
Verify = bool
Hooks = List[Union[Text, Dict[Text, Text]]]
Export = List[Text]
Validators = List[Dict]
Env = Dict[Text, Any]


class MethodEnum(Text, Enum):
    """
    枚举请求方法，定义了常用的http请求方法
    """
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"


class TConfig(BaseModel):
    """
    定义配置信息，包含如下：
    1.name      （str）
    2.verify    （bool）
    3.base_url  （http/https开头的str类型）
    4.variables （dict）
    5.parameters（dict）
    6.export    （list[str]）
    7.path      （str）
    8.weight    （int）
    """
    name: Name
    verify: Verify = False
    base_url: BaseUrl = ""
    # Text: prepare variables in debugtalk.py, ${gen_variables()}
    variables: Union[VariablesMapping, Text] = {}
    parameters: Union[VariablesMapping, Text] = {}
    # setup_hooks: Hooks = []
    # teardown_hooks: Hooks = []
    export: Export = []
    path: Text = None
    weight: int = 1


class TRequest(BaseModel):
    """
    requests.Request model

    1.method  （枚举类型）
    2.url     （str）
    3.params  （dict）
    4.headers （dict）
    5.req_json（dict/list/str）
    6.data    （dict/str）
    7.cookie  （dict）
    8.timeout （float）
    9.allow_redirects （bool）
    10.verify （bool）
    11.upload （dict）
    """

    method: MethodEnum
    url: Url
    params: Dict[Text, Text] = {}
    headers: Headers = {}
    req_json: Union[Dict, List, Text] = Field(None, alias="json")
    data: Union[Text, Dict[Text, Any]] = None
    cookies: Cookies = {}
    timeout: float = 120
    allow_redirects: bool = True
    verify: Verify = False
    upload: Dict = {}  # used for upload files


class TStep(BaseModel):
    """
    测试步骤，里面包含了request请求

    1.name              （str）
    2.request           （TRequest）
    3.testcase          （str/Callable）
    4.variables         （dict）
    5.setup_hooks       （list(dict)）
    6.teardown_hooks    （list(dict)）
    7.extract           （dict）
    8.export            （list）
    9.validators        （list(dict)）
    10.validate_script  （list[str]）
    """
    name: Name
    request: Union[TRequest, None] = None
    testcase: Union[Text, Callable, None] = None
    variables: VariablesMapping = {}
    setup_hooks: Hooks = []
    teardown_hooks: Hooks = []
    # used to extract request's response field
    extract: VariablesMapping = {}
    # used to export session variables from referenced testcase
    export: Export = []
    validators: Validators = Field([], alias="validate")
    validate_script: List[Text] = []


class TestCase(BaseModel):
    """
    测试用例，包含了测试步骤和配置信息
    """
    config: TConfig
    teststeps: List[TStep]


class ProjectMeta(BaseModel):
    """
    项目结构
    1.debugtalk_py   （str）                   debugtakl文件内容
    2.debugtalk_path （str）                   debugtalk文件路径
    3.dot_env_path   （str）                   env文件路径
    4.functions      （dict(Callable/str)）    在debugtalk中定义的函数
    5.env            （dict）                  环境
    6.RootDir        （str）                   根路径（绝对路径），debugtalk位于的路径
    """
    debugtalk_py: Text = ""  # debugtalk.py file content
    debugtalk_path: Text = ""  # debugtalk.py file path
    dot_env_path: Text = ""  # .env file path
    functions: FunctionsMapping = {}  # functions defined in debugtalk.py
    env: Env = {}
    RootDir: Text = os.getcwd()  # project root directory (ensure absolute), the path debugtalk.py located


class TestsMapping(BaseModel):
    """
    测试映射
    1.project_meta
    2.testcases 测试用例集，list下有多个用例
    """
    project_meta: ProjectMeta
    testcases: List[TestCase]


class TestCaseTime(BaseModel):
    """
    测试用例时间

    1.start_at：开始时间默认为0
    2.start_at_iso_format：以iso格式启动
    3.duration：持续时间
    """
    start_at: float = 0
    start_at_iso_format: Text = ""
    duration: float = 0


class TestCaseInOut(BaseModel):
    """
    测试用例的输入输出：

    config_vars：配置变量
    export_vars：导出变量
    """
    config_vars: VariablesMapping = {}
    export_vars: Dict = {}


class RequestStat(BaseModel):
    """
    请求指标：

    content_size：内容大小
    response_time_ms：响应时间(ms)
    elapsed_ms：逝去的时间(ms)
    """
    content_size: float = 0
    response_time_ms: float = 0
    elapsed_ms: float = 0


class AddressData(BaseModel):
    """
    客户端与服务器地址数据

    client_ip：客户端ip地址
    client_port：客户端端口号
    server_ip：服务器ip地址
    server_port：服务器端口号
    """
    client_ip: Text = "N/A"
    client_port: int = 0
    server_ip: Text = "N/A"
    server_port: int = 0


class RequestData(BaseModel):
    """
    请求数据

    method：请求方法，默认为GET
    url：url地址
    headers：请求头
    cookies：cookie信息
    body：请求体
    """
    method: MethodEnum = MethodEnum.GET
    url: Url
    headers: Headers = {}
    cookies: Cookies = {}
    body: Union[Text, bytes, List, Dict, None] = {}


class ResponseData(BaseModel):
    """
    响应数据

    status_code：状态码
    headers：响应头
    cookies：cookie信息
    encoding：编码格式
    content_type：内容类型
    body：响应体
    """
    status_code: int
    headers: Dict
    cookies: Cookies
    encoding: Union[Text, None] = None
    content_type: Text
    body: Union[Text, bytes, List, Dict]


class ReqRespData(BaseModel):
    """
    请求响应数据
    request：RequestData
    response：ResponseData
    """
    request: RequestData
    response: ResponseData


class SessionData(BaseModel):
    """
    request session data, including request, response, validators and stat data
    """

    success: bool = False
    # in most cases, req_resps only contains one request & response
    # while when 30X redirect occurs, req_resps will contain multiple request & response
    req_resps: List[ReqRespData] = []
    stat: RequestStat = RequestStat()
    address: AddressData = AddressData()
    validators: Dict = {}


class StepData(BaseModel):
    """
    teststep data, each step maybe corresponding to one request or one testcase
    测试步骤数据，每个步骤可能对应一个请求或一个测试用例
    """

    success: bool = False
    name: Text = ""  # teststep name
    data: Union[SessionData, List['StepData']] = None
    export_vars: VariablesMapping = {}

        
StepData.update_forward_refs()


class TestCaseSummary(BaseModel):
    """
    测试用例结果

    name：测试用例名字
    success：测试用例成功的状态
    case_id：测试用例的id
    time：测试用例的时间
    in_out：测试用例的导入导出数据
    log：测试用例的日志
    step_datas：测试步骤的数据
    """
    name: Text
    success: bool
    case_id: Text
    time: TestCaseTime
    in_out: TestCaseInOut = {}
    log: Text = ""
    step_datas: List[StepData] = []


class PlatformInfo(BaseModel):
    """
    平台信息

    httprunner_version：httprunner版本号
    python_version：python版本
    platform：平台
    """
    httprunner_version: Text
    python_version: Text
    platform: Text


class TestCaseRef(BaseModel):
    """
    包含testcase
    """
    name: Text
    base_url: Text = ""
    testcase: Text
    variables: VariablesMapping = {}


class TestSuite(BaseModel):
    """
    测试套件
    TestSuite包含TestCaseRef
    TestCaseRef包含testcase
    """
    config: TConfig
    testcases: List[TestCaseRef]


class Stat(BaseModel):
    """
    统计信息

    total：总数
    success：成功的用例数
    fail：失败的用例数
    """
    total: int = 0
    success: int = 0
    fail: int = 0


class TestSuiteSummary(BaseModel):
    """
    测试套件结果

    success：成功的状态
    stat：统计信息
    time：测试用例花费的时间
    platform：平台信息
    testcases：测试用例集
    """
    success: bool = False
    stat: Stat = Stat()
    time: TestCaseTime = TestCaseTime()
    platform: PlatformInfo
    testcases: List[TestCaseSummary]
