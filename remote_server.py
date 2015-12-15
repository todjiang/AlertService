# encoding=utf-8
from random import randint

import simplejson
import web
import requests
import yaml

from wechat.enterprise import WxApplication, WxApi
from wechat.enterprise import WxTextResponse
from wechat.models import WxEmptyResponse

urls = (
  '/', 'WeChatHandler',
  '/pp', 'PushListener'
)

ISSUES = []

# mock issue id for demo
RANDOM_ISSUE_IDS = ['00015', '00016', '00017', '00018', '00019']


with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)


def send_to_all(req, msg):
    api = WxApi(cfg['CORP_ID'], cfg['SECRET'])
    api.send_text(msg, req.AgentID, '0', '@all')
    return WxEmptyResponse()


class WxApp(WxApplication):
    def __init__(self):
        self.SECRET_TOKEN = cfg['SECRET_TOKEN']
        self.ENCODING_AES_KEY = cfg['ENCODING_AES_KEY']
        self.CORP_ID = cfg['CORP_ID']

# text event format:
# <xml>
# <ToUserName><![CDATA[todjiang]]></ToUserName>
# <FromUserName><![CDATA[wx6e07daeda81c6fd3]]>
# </FromUserName><CreateTime>1449147623</CreateTime>
# <MsgType><![CDATA[text]]></MsgType>
# <Content><![CDATA[ack]]></Content>
# </xml>
    def on_text(self, req):
        if req.Content.find(' ') != -1:
            msgs = req.Content.split(' ')
            action = msgs[0].lower()
            if action == 'ack':
                return self.follow_up(req, msgs[1])
            elif action == 'fix':
                return self.resolve_issue(req, msgs[1])
            else:
                return WxTextResponse('Unknown command', req)
        else:
            action = req.Content.lower()
            if action == 'ack':
                self.follow_up(req)
            elif action == 'fix':
                return self.resolve_issue(req)
            else:
                return WxTextResponse('Unknown command', req)

# click event format:
# <xml><ToUserName><![CDATA[wx6e07daeda81c6fd3]]></ToUserName>
# <FromUserName><![CDATA[todjiang]]></FromUserName>
# <CreateTime>1449122502</CreateTime>
# <MsgType><![CDATA[event]]></MsgType>
# <AgentID>3</AgentID>
# <Event><![CDATA[click]]></Event>
# <EventKey><![CDATA[1]]></EventKey>
# </xml>
    def on_event(self, req):
        if req.EventKey == "0":
            return self.create_issue(req)
        elif req.EventKey == '1':
            return self.follow_up(req)
        elif req.EventKey == '2':
            return self.resolve_issue(req)
        else:
            print 'Unexpected Event Key...'
            return WxEmptyResponse()

    @staticmethod
    def create_issue(req):
        random_issue_id = RANDOM_ISSUE_IDS[randint(0, 4)]

        requests.post('http://127.0.0.1/pp', data=simplejson.dumps({'tid': req.AgentID, 'iid': random_issue_id}))

        return send_to_all(req, '\n'.join([req.FromUserName + ' posted an issue...', 'ID: ' + random_issue_id,
                                 'Name: LIVE DB CONNECTION', 'Level: P0', 'Description: CONF DB down']))

    @staticmethod
    def follow_up(req, issue_id=None):
        print ISSUES

        for i in ISSUES:
            if req.AgentID == i['tid']:
                if issue_id:
                    if issue_id in i['issue_list']:
                        return send_to_all(req, ' '.join(['Issue', issue_id, 'is followed up by', req.FromUserName]))
                    else:
                        return WxTextResponse('Issue ' + issue_id + ' not found', req)
                else:
                    if len(i['issue_list']) == 1:
                        return send_to_all(req, ' '.join(['Issue', i['issue_list'][0], 'is followed up by', req.FromUserName]))
                    elif len(i['issue_list']) > 1:
                        return WxTextResponse("Multiple issues found, please type msg format: \"ack ISSUE_ID\"", req)
                    else:
                        # issue list length == 0
                        return WxTextResponse('No issue found...', req)

        return WxTextResponse('No issue found...', req)

    @staticmethod
    def resolve_issue(req, issue_id=None):
        print ISSUES

        for i in ISSUES:
            if req.AgentID == i['tid']:
                if issue_id:
                    if issue_id in i['issue_list']:
                        i['issue_list'].remove(issue_id)
                        return send_to_all(req, ' '.join(['Issue', issue_id, 'is fixed by', req.FromUserName]))
                    else:
                        return WxTextResponse('Issue ' + issue_id + ' not found', req)
                else:
                    if len(i['issue_list']) == 1:
                        ISSUES.remove(i)
                        return send_to_all(req, ' '.join(['Issue', i['issue_list'].pop(), 'is fixed by', req.FromUserName]))

                    elif len(i['issue_list']) > 1:
                        return WxTextResponse("Multiple issues found, please type msg format: \"fix ISSUE_ID\"", req)
                    else:
                        # issue list length == 0
                        return WxTextResponse('No issue found...', req)

        return WxTextResponse('No issue found...', req)


class WeChatHandler:
    def __init__(self):
        pass

    # WeChat URL verification
    def GET(self):
        input_parameters = web.input()

        if len(input_parameters) == 0:
            return web.Unauthorized()

        echo = WxApp()
        echo_str = echo.process(input_parameters, xml=None)
        return echo_str

    # Call back URL for WeChat
    def POST(self):
        input_parameters = web.input()
        input_data = web.data()

        if len(input_parameters) == 0 or len(input_data) == 0:
            return web.Unauthorized()

        wx_callback = WxApp()
        return wx_callback.process(input_parameters, input_data)


class PushListener:
    def __init__(self):
        pass

    # Call back URL for WeChat
    def POST(self):
        input_data = web.data()
        if len(input_data) == 0:
            return web.BadRequest()

        json_data = simplejson.loads(input_data)

        for i in ISSUES:
            if json_data['tid'] == i['tid']:
                i['issue_list'].append(json_data['iid'])
                return

        # if not found, create a init issue list
        ISSUES.append({'tid': json_data['tid'], 'issue_list': [json_data['iid']]})
        return web.OK


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
