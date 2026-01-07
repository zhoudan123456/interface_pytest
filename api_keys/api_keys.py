import jsonpath

from requests import request, Session

from conf.set_conf import read_conf, write_conf


class ApiKeys:

    def __init__(self,env):
        self.env = env
        self.session = Session()
        # 设置默认headers
        self.session.headers.update({
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/137.0.0.0 Safari/537.36'
        })


    def request(self, method, path=None, headers=None, save_cookie=False, **kwargs):
        url = self.set_url(path)
        # 更新session的headers
        if headers:
            self.session.headers.update(headers)
        
        # 如果有token，添加到Authorization header
        if read_conf('data', 'token'):
            token = read_conf('data', 'token')
            self.session.headers.update({'Authorization': token})
        
        res = self.session.request(method=method, url=url, **kwargs)
        

        return res

    def set_url(self, path):
        host = read_conf(self.env, 'host')
        # 确保host没有末尾的斜杠
        if host.endswith('/'):
            host = host[:-1]
        # 确保path有开头的斜杠
        if path and not path.startswith('/'):
            path = '/' + path
        elif not path:
            path = ''
        url = host + path
        return url




    def get_values(self, res, key):

        values = jsonpath.jsonpath(res, f'$..{key}')

        if len(values) == 1:
            return values[0]

        else:
            return values



    def assert_text(self,expected,res,key):
        reality = self.get_values(res,key)
        assert expected == reality,f'''
        预期结果：{expected}
        实际结果：{reality}
        断言结果：{expected} != {reality}

'''
