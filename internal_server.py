# encoding=utf-8
import simplejson
import web
import yaml
import requests

from wechat.enterprise import WxApi
from incoming import datatypes, PayloadValidator


class Index:
    def __init__(self):
        pass

    def GET(self):
        return "Alert Service"


with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)


class IssueValidator(PayloadValidator):
    ID = datatypes.String()
    Name = datatypes.String()
    Level = datatypes.String()
    Description = datatypes.String()


class RaiseAlert:
    def POST(self):
        try:
            tid_value = web.input()['tid']
        except KeyError:
            return web.BadRequest()

        try:
            team_id = cfg['TEAM_ID_DICT'][tid_value.upper()]
        except KeyError:
            return web.Unauthorized()

        if len(web.data()) == 0:
            return web.BadRequest()

        data = simplejson.loads(web.data())
        # json validation
        good, errors = IssueValidator().validate(data)
        if not good:
            return errors

        r = requests.post(''.join(['http://', cfg['REMOTE_HOST'], '/pp']), data=simplejson.dumps({'tid': str(team_id), 'iid': data['ID']}))
        if r.status_code != 200:
            print 'Call remote server failed...'
            print r.text

        api = WxApi(cfg['CORP_ID'], cfg['SECRET'])
        api.send_text(self.build_msg(data), team_id, 0, '@all')

        return web.OK('ok')

    @staticmethod
    def data_normalize(data):
        return simplejson.loads(data)

    @staticmethod
    def build_msg(data):
        # TODO re-factory
        return '\n'.join(['ID: ' + data['ID'], 'Name: ' + data['Name'], 'Level: ' + data['Level'], 'Description: ' + data['Description']])


class RaiseAlertRawText:
    def POST(self):
        try:
            tid_value = web.input()['tid']
        except KeyError:
            return web.BadRequest()

        try:
            team_id = cfg['TEAM_ID_DICT'][tid_value.upper()]
        except KeyError:
            return web.Unauthorized()

        if len(web.data()) == 0:
            return web.BadRequest()

        api = WxApi(cfg['CORP_ID'], cfg['SECRET'])
        api.send_text(web.data(), team_id, 0, '@all')

        return web.OK('ok')


def not_found():
    return web.notfound("Sorry, the page you were looking for was not found.")


def internal_error():
    return web.internalerror('Internal Server Error...')


urls = (
    '/', 'Index',
    '/raise_alert', 'RaiseAlert',
    '/raise_alert_raw_text', 'RaiseAlertRawText',
    '/alert', 'RaiseAlertRawText'
)


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.notfound = not_found
    app.internalerror = internal_error
    app.run()
