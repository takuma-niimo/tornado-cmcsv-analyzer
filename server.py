#!/bin/env python
# -*- coding: utf-8 -*-
import json, os, uuid, csv, re, pprint
import tornado
import tornado.ioloop
import tornado.web

def remarks_analyze(txt):
  atena = ''
  tadashi = ''
  if txt == '':
    return atena, tadashi

  m = re.search(r'あて名　：【.*?】', txt)
  if m:
    atena = m.group()
  else:
    atena = ''
  atena = atena[6:-1]

  m = re.search(r'但し書き：【.*?】', txt)
  if m:
    tadashi = m.group()
  else:
    tadashi = ''
  tadashi = tadashi[6:-1]

  return atena, tadashi

def csvanalyzer(csvdic):
  num = []
  name = []
  name2 = []
  what = []
  for row in csvdic:
    res = remarks_analyze(row['備考'])
    num.append(row['管理番号'])
    name.append(row['注文者氏名'])
    name2.append(res[0])
    what.append(res[1])

  return num, name, name2, what


class Userform(tornado.web.RequestHandler):
  def get(self):
    self.render(
      'fileuploadform.html'
    )

class Upload(tornado.web.RequestHandler):
  def post(self):
    fileinfo = self.request.files['filearg'][0]
    csvtxt = fileinfo['body'].decode('shift_jis', 'ignore')
    csvdic = [{k: v for k, v in row.items()} for row in csv.DictReader(csvtxt.splitlines(), skipinitialspace=True)]
    (num, name, name2, what) = csvanalyzer(csvdic)
    self.render(
      'result.html',
      ta = num,
      tb = name,
      tc = name2,
      td = what
    )
    #self.finish()


BASE_DIR = os.path.dirname(__file__)

application = tornado.web.Application([
  (r"/", Userform),
  (r"/upload", Upload),
  ],
  template_path = os.path.join(BASE_DIR, 'templates'),
  static_path = os.path.join(BASE_DIR, 'static'),
  debug=True)


if __name__ == "__main__":
  application.listen(8888)
  tornado.ioloop.IOLoop.instance().start()
