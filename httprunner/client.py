# 客户端相关方法,主要是封装 requests.Session.request,安全调用,输出log等, 给runner.py调用.

import json
import time

import requests
import urllib3
from loguru import logger
from requests import Request, Response
from requests.exceptions import (
    InvalidSchema,
    InvalidURL,
    MissingSchema,
    RequestException,
)

from httprunner.models import RequestData, ResponseData
from httprunner.models import SessionData, ReqRespData
from httprunner.utils import lower_dict_keys, omit_long_data

# 屏蔽https证书警告
"""
使用Python3 requests发送HTTPS请求，已经关闭认证（verify=False）情况下，控制台会输出错误。在代码中禁用安全请求警告
"""
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ApiResponse(Response):
    """
    继承了requests模块中的Response类，重写 raise_for_status 状态码异常方法
    """
    def raise_for_status(self):
        # hasattr() 函数用于判断对象是否包含对应的属性
        if hasattr(self, "error") and self.error:
            raise self.error
        Response.raise_for_status(self)


def get_req_resp_record(resp_obj: Response) -> ReqRespData:
    """
    从 Response()对象获取请求记录和响应记录

    :param resp_obj: Response响应
    :return: 返回自定义的ReqResData模型类
    """

    def log_print(req_or_resp, r_type):
        """
        日志打印，格式为标准的json
        """
        msg = f"\n================== {r_type} details ==================\n"
        for key, value in req_or_resp.dict().items():
            # 如果value中还包含着dict或者list，就把value转成json格式
            if isinstance(value, dict) or isinstance(value, list):
                # json.dumps 序列化时对中文默认使用的ascii编码,因此需要使用ensure_ascii=False来指定出中文
                """
                indent=4 表示每行缩进4字字节
                {'age': 4, 'name': 'niuniuche', 'attribute': 'toy'}
                {
                    "age": 4,
                    "name": "niuniuche",
                    "attribute": "toy"
                }
                """
                value = json.dumps(value, indent=4, ensure_ascii=False)

            msg += "{:<8} : {}\n".format(key, value)
        logger.debug(msg)

    # 记录实际请求信息（请求头、cookie信息、请求体）
    request_headers = dict(resp_obj.request.headers)
    request_cookies = resp_obj.request._cookies.get_dict()

    request_body = resp_obj.request.body
    if request_body is not None:
        try:
            request_body = json.loads(request_body)
        except json.JSONDecodeError:
            # str: a=1&b=2
            pass
        except UnicodeDecodeError:
            # bytes/bytearray: request body in protobuf
            pass
        except TypeError:
            # neither str nor bytes/bytearray, e.g. <MultipartEncoder>
            pass

        # lower_dict_keys的作用是将字典中的key大写转小写
        request_content_type = lower_dict_keys(request_headers).get("content-type")
        if request_content_type and "multipart/form-data" in request_content_type:
            # upload file type
            request_body = "upload file stream (OMITTED)"

    request_data = RequestData(
        method=resp_obj.request.method,
        url=resp_obj.request.url,
        headers=request_headers,
        cookies=request_cookies,
        body=request_body,
    )

    log_print(request_data, "request")

    # 记录响应信息
    resp_headers = dict(resp_obj.headers)
    lower_resp_headers = lower_dict_keys(resp_headers)
    content_type = lower_resp_headers.get("content-type", "")

    if "image" in content_type:
        # response is image type, record bytes content only
        # 二进制内容获取
        response_body = resp_obj.content
    else:
        try:
            # try to record json data
            response_body = resp_obj.json()
        except ValueError:
            # only record at most 512 text charactors
            resp_text = resp_obj.text
            # 长度处理
            response_body = omit_long_data(resp_text)

    # 实例化ResponseData模型
    response_data = ResponseData(
        status_code=resp_obj.status_code,
        cookies=resp_obj.cookies or {},
        encoding=resp_obj.encoding,
        headers=resp_headers,
        content_type=content_type,
        body=response_body,
    )

    # 在debug模式下打印响应日志
    log_print(response_data, "response")

    # 实例化ReqRespData 其就是 RequestData ResponseData 组成
    req_resp_data = ReqRespData(request=request_data, response=response_data)
    return req_resp_data

# 继承requests.Session
class HttpSession(requests.Session):
    """
    Class for performing HTTP requests and holding (session-) cookies between requests (为了
    能够登录和退出网站). 每个请求都被记录下来，这样HttpRunner就可以显示统计数据。

    This is a slightly extended version of `python-request <http://python-requests.org>`_'s
    :py:class:`requests.Session` class and mostly this class works exactly the same.
    """

    def __init__(self):
        super(HttpSession, self).__init__()
        self.data = SessionData()

    def update_last_req_resp_record(self, resp_obj):
        """
        更新最新的请求响应记录，放入req_resps列表中
        """
        # TODO: fix
        self.data.req_resps.pop()
        self.data.req_resps.append(get_req_resp_record(resp_obj))

    def _send_request_safe_mode(self, method, url, **kwargs):
        """
        发送一个http请求，并捕获由于连接问题可能发生的任何异常
        Safe mode has been removed from requests 1.x.
        """
        try:
            return requests.Session.request(self, method, url, **kwargs)
        except (MissingSchema, InvalidSchema, InvalidURL):
            raise
        except RequestException as ex:
            resp = ApiResponse()
            resp.error = ex
            resp.status_code = 0  # with this status_code, content returns None
            resp.request = Request(method, url).prepare()
            return resp

    def request(self, method, url, name=None, **kwargs):
        """
        1.设置了超时时间120s
        2.计算整个请求花费了多少时间
        3.定义了客户端ip地址和端口号、服务端ip地址和端口号
        4.计算了响应体的内容大小
        5.记录了消耗时间
        6.记录了request和response记录，包括重定向记录
        """

        """
        Constructs and sends a :py:class:`requests.Request`.
        Returns :py:class:`requests.Response` object.

        :param method:
            method for the new :class:`Request` object.
        :param url:
            URL for the new :class:`Request` object.
        :param name: (optional)
            Placeholder, make compatible with Locust's HttpSession
        :param params: (optional)
            Dictionary or bytes to be sent in the query string for the :class:`Request`.
        :param data: (optional)
            Dictionary or bytes to send in the body of the :class:`Request`.
        :param headers: (optional)
            Dictionary of HTTP Headers to send with the :class:`Request`.
        :param cookies: (optional)
            Dict or CookieJar object to send with the :class:`Request`.
        :param files: (optional)
            Dictionary of ``'filename': file-like-objects`` for multipart encoding upload.
        :param auth: (optional)
            Auth tuple or callable to enable Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional)
            How long to wait for the server to send data before giving up, as a float, or \
            a (`connect timeout, read timeout <user/advanced.html#timeouts>`_) tuple.
            :type timeout: float or tuple
        :param allow_redirects: (optional)
            Set to True by default.
        :type allow_redirects: bool
        :param proxies: (optional)
            Dictionary mapping protocol to the URL of the proxy.
        :param stream: (optional)
            whether to immediately download the response content. Defaults to ``False``.
        :param verify: (optional)
            if ``True``, the SSL cert will be verified. A CA_BUNDLE path can also be provided.
        :param cert: (optional)
            if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
        """
        self.data = SessionData()

        # 设置了超时时间120s
        kwargs.setdefault("timeout", 120)

        # set stream to True, in order to get client/server IP/Port
        kwargs["stream"] = True

        # 计算整个请求花费了多少时间
        start_timestamp = time.time()
        response = self._send_request_safe_mode(method, url, **kwargs)
        """
        round() 方法返回浮点数x的四舍五入值
        round( x [, n]  )
        x -- 数值表达式。
        n -- 数值表达式，表示从小数点位数。
        """
        response_time_ms = round((time.time() - start_timestamp) * 1000, 2)

        # 定义了客户端ip地址和端口号、服务端ip地址和端口号
        try:
            client_ip, client_port = response.raw.connection.sock.getsockname()
            self.data.address.client_ip = client_ip
            self.data.address.client_port = client_port
            logger.debug(f"client IP: {client_ip}, Port: {client_port}")
        except AttributeError as ex:
            logger.warning(f"failed to get client address info: {ex}")

        try:
            server_ip, server_port = response.raw.connection.sock.getpeername()
            self.data.address.server_ip = server_ip
            self.data.address.server_port = server_port
            logger.debug(f"server IP: {server_ip}, Port: {server_port}")
        except AttributeError as ex:
            logger.warning(f"failed to get server address info: {ex}")

        # 计算了响应体的内容大小
        content_size = int(dict(response.headers).get("content-length") or 0)

        # 记录了消耗时间
        self.data.stat.response_time_ms = response_time_ms
        self.data.stat.elapsed_ms = response.elapsed.microseconds / 1000.0
        self.data.stat.content_size = content_size

        # 记录了request和response记录，包括重定向记录
        response_list = response.history + [response]
        self.data.req_resps = [
            get_req_resp_record(resp_obj) for resp_obj in response_list
        ]

        try:
            response.raise_for_status()
        except RequestException as ex:
            logger.error(f"{str(ex)}")
        else:
            logger.info(
                f"status_code: {response.status_code}, "
                f"response_time(ms): {response_time_ms} ms, "
                f"response_length: {content_size} bytes"
            )

        return response

if __name__ == '__main__':
    url = "https://www.baidu.com"
    response = requests.get(url)
    re_raw = response.raw.connection.sock
    print(re_raw)
    # response.raw.connection.sock.getsockname()
