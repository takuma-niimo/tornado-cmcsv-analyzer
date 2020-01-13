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


class receiptSheetForm(tornado.web.RequestHandler):
  """
  @class receiptSheetForm
  @brief リクエストを受けたら receiptSheet/form.html を返す
  """

  def get(self):
    self.render(
      'receiptSheet/form.html'
    )

class receiptSheetUpload(tornado.web.RequestHandler):
  """
  @class receiptSheetUpload
  @brief POSTでCSVデータをもらう
  @details POSTで受けたデータを分析して receiptSheet/result.html でレンダリングする
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
      'receiptSheet/result.html',
      ta = num,
      tb = name,
      tc = name2,
      td = what
    )
    #self.finish()

class addQuantityB2csvForm(tornado.web.RequestHandler):
  """
  @class addQuantityB2csvForm
  @brief item.csv, order.csv をもとに delivery_list.csv の品目に個数を追加する
  """

  def get(self):
    self.render(
      'addQuantityB2csv/form.html'
    )

def addQ(o, i, dd, dt):
  dlist = dt.split('\n')
  output = []
  output.append(dlist[0])
  for drow in dd:
    dnum = drow['お客様管理番号']
    dpname1 = drow['品名１']
    dpname2 = drow['品名２']
    code1 = []
    code2 = []
    quantity1 = ''
    quantity2 = ''

    # item.csv から商品コードを検索
    if dpname1 != '':
      for irow in i:
        if irow['品目'] == dpname1:
          code1.append(irow['商品コード'])

    if dpname2 != '':
      for irow in i:
        if irow['品目'] == dpname2:
          code2.append(irow['商品コード'])

    if code1 == '' and code2 == '':
      output.append(drow)
      continue

    # order.csv から商品コードに一致する行の数量を検索
    for orow in o:
      if orow['管理番号'] == dnum:
        for code in code1:
          if code == orow['商品コード']:
            quantity1 = orow['数量']
        for code in code2:
          if code ==  orow['商品コード']:
            quantity2 = orow['数量']

    # B2用CSVの「品名」行書き換え
    for dlistrow in dlist:
      if dnum in dlistrow:
        if dpname1 != '' and quantity1 != '1':
          r = quantity1 + ')' + dpname1
          dlistrow  = dlistrow.replace(dpname1, r)
        if dpname2 != '' and quantity2 != '1':
          r = quantity2 + ')' + dpname2
          dlistrow = dlistrow.replace(dpname2, r)
        output.append(dlistrow)
        break

  dtxt = '\n'.join(output)

  return dtxt


class addQuantityB2csvUpload(tornado.web.RequestHandler):
  def post(self):
    orderinfo     = self.request.files['order'][0]
    iteminfo      = self.request.files['item'][0]
    deliveryinfo  = self.request.files['delivery'][0]

    (oname, iname, dname) = \
      (orderinfo['filename'], iteminfo['filename'], deliveryinfo['filename'])

    oTxt = orderinfo['body'].decode('shift_jis', 'ignore')
    iTxt = iteminfo['body'].decode('shift_jis', 'ignore')
    dTxt = deliveryinfo['body'].decode('shift_jis', 'ignore')

    odic = [{k: v for k, v in row.items()} for row in csv.DictReader(oTxt.splitlines(), skipinitialspace=True)]
    idic = [{k: v for k, v in row.items()} for row in csv.DictReader(iTxt.splitlines(), skipinitialspace=True)]
    ddic = [{k: v for k, v in row.items()} for row in csv.DictReader(dTxt.splitlines(), skipinitialspace=True)]

    csvtxt = addQ(odic, idic, ddic, dTxt)

    self.set_header('Content-Type', "text/csv")
    self.set_header('Content-Disposition',
        "attachment; filename=\"{}\"".format('addQ_' + dname))
    self.set_header('Content-Length', len(csvtxt.encode('shift_jis')))
    self.write(csvtxt.encode('shift_jis'))

class Welcome(tornado.web.RequestHandler):
  """
  @class Welcome
  @brief ウェルカム画面
  """

  def get(self):
    self.render(
      'welcome.html'
    )

BASE_DIR = os.path.dirname(__file__)

application = tornado.web.Application([
  (r"/", Welcome),
  (r"/receiptForm", receiptSheetForm),  # 領収書が必要かどうか判別する機能
  (r"/receiptUpload", receiptSheetUpload),
  (r"/addQuantityB2csvForm", addQuantityB2csvForm),
  (r"/addQuantityB2csvUpload", addQuantityB2csvUpload),
  ],
  template_path = os.path.join(BASE_DIR, 'templates'),
  static_path = os.path.join(BASE_DIR, 'static'),
  debug=True)


if __name__ == "__main__":
  application.listen(8888)
  tornado.ioloop.IOLoop.instance().start()
