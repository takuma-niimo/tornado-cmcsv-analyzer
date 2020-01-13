#!/bin/env python
# -*- coding: utf-8 -*-
import os, csv, re, pprint, sys
import tornado
import tornado.ioloop
import tornado.web

def remarks_analyze(txt):
  """
  @fn             remarks_analyze()
  @brief          ひとつの備考テキストデータから、領収書の宛名と但書の組を返す
  @param txt      備考テキストデータ
  @retval atena   宛名テキスト
  @retval tadashi 但書テキスト
  """

  atena = ''
  tadashi = ''
  if txt == '':
    return atena, tadashi

  m = re.search(r'あて名　：【.*?】', txt)
  if m:
    atena = m.group()
    atena = atena[6:-1]
  else:
    atena = ''

  m = re.search(r'但し書き：【.*?】', txt)
  if m:
    tadashi = m.group()
    tadashi = tadashi[6:-1]
  else:
    tadashi = ''

  return atena, tadashi

def csvanalyzer(csvdic):
  """
  @fn           csvanalyzer()
  @brief        CSVを解析して、[管理番号, 氏名, 宛名, 但書]の組を返す
  @detail       ただし管理番号が同一のものはスキップする
  @param csvdic CSVデータ(辞書型)
  @retval num   管理番号
  @retval name  氏名
  @retval name2 領収書の宛名
  @retval what  領収書の但し書き
  """

  num = []
  name = []
  name2 = []
  what = []
  NUM = ''

  for row in csvdic:
    if NUM == row['管理番号']:
      continue
    res = remarks_analyze(row['備考'])
    num.append(row['管理番号'])
    name.append(row['注文者氏名'])
    name2.append(res[0])
    what.append(res[1])
    NUM = row['管理番号']

  return num, name, name2, what


class Userform(tornado.web.RequestHandler):
  """
  @class Userform
  @brief リクエストを受けたら fileuploadform.html を返す
  """

  def get(self):
    self.render(
      'fileuploadform.html'
    )

class Upload(tornado.web.RequestHandler):
  """
  @class Upload
  @brief POSTでCSVデータをもらう
  @details POSTで受けたデータを分析して result.html でレンダリングする
  @warning warning
  @note note
  """

  def post(self):
    """
    @fn         post()
    @brief      POSTでCSVデータをもらう
    @param self リクエスト自身
    @return     None
    """

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
