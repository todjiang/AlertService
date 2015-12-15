# AlertService
A simple RESTful service base on WeChat enterprise account

基于python封装的WeChat SDK,  微信官方的sample过于简单，用别人封装好的东西， 上手会更快点。
我使用过程中也遇到一些小小问题， 不过源码摆那， 修改一下就基本上没问题了。

WeChat 官方python sample, 见目录 python

网上各种语言SDK已经很多, 我就选个python的, 见目录 wechat

Jeff WeChat
https://github.com/jeffkit/wechat


使用web.py的搭建restful serivice, 原因也就是简单，上手快。

如果只是想用来发消息， 只用internal_server.py的send raw data接口就行了。 如果有用到回调功能与用户互动了，那么在公网搞台机器（各种云选一个。。）
remote server 在我这里例子里用来记录issue的跟进和解决的状态。

## Installation:
ubuntu OS
```
apt-get install python-dev  
python-dev for compile pycrypto
pip install requests web.py pycrypto pyyaml incoming 
```

pyyaml:  yml config read

incoming: json validation



##Service Usage:

HTTP Method: POST
tid is the unique id for a team

Json data sender, restrict data format:
URL: http://localhost:8080/raise_alert?tid=test

Body Content:
```
{
    "ID": "00002",
    "Name": "LIVE DB CONNECTION",
    "Level": "P0",
    "Description": "CONF DB down"
}

```

RawData sender:
URL: http://localhost:8080/raise_alert_raw_text?tid=test


###Issue tracking:
Click “FollowUp” or “Resolved” for an existing issue, tracking issue status for a team.

For multiple issues, type command:
```
	ack ISSUE_ID
	fix ISSUE_ID
```
