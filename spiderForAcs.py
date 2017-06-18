# coding=utf-8
# 用于爬取JACS上的文章，包括以下内容：
# 文章标题， 文章作者， 文章配图， 文章摘要， 出版日期， DOI信息
'''
项目思路：
1. 打开网址，获取网页源码
2. 从网页源码中匹配出所要的超链接
  从源码中匹配正则表达式所指定的内容



'''

import requests  # 爬虫的一个模块处理网络请求模块
from bs4 import BeautifulSoup
import re
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')  # 输出内容文件编码


class Spider(object):
    # ACS
    acsUrl = "http://pubs.acs.org"

    def __init__(self):
        super(Spider, self).__init__()

    # JACS的设定为：一年为一期
    # JACS全部的期数，即从发行到现在的所有年数
    # volumeDirect{}
    # volumeDirect{年份 期刊数1：[全部巻号数列表1]， 期刊数2：[全部巻号数列表2], ....}
    def getAllVolumeDirect(self, listOfIssuesURL):
      # 定义一个期数字典，初始为空{期数：[全部巻号数列表]}
      volumeDirect = {}
      # 获取JACS期刊目录网页soup对象
      soup = self.getWebSourceSoup(listOfIssuesURL)
      # 取得全部期数
      volumeNum = soup.select('a.opener')
      for index in volumeNum:
        # 取出文本字符串并去除两端所有空格/换行
        a = index.text.strip()
        year = a.split(": ")[0]
        volume = a.split(": ")[1].split(" ")[1]
        # 取得指定期数下全部的巻号数
        issueTemp = soup.select('div#volume' + volume + ' div.block div.row a')
        # 定义一个巻号数列表,存放每一期中全部的巻号数
        issumeList = []
        for temp in issueTemp:
          # 字符串操作，第序号为6的字符串，然后取该字符串下标为1开始到最后第2个之间的字符，即巻号
          issue = temp.text.split()[6][0:-1]
          # 将巻号数保存为列表
          if issue not in issumeList:
            issumeList.append(issue)
        # 将巻号数和期数关联
        volumeDirect[year + ' ' + volume] = issumeList
      return volumeDirect

    # 获取网站源码并包装成BeautifulSoup类对象
    def getWebSourceSoup(self, url):
        # 浏览器头部信息
        header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        # 创建requests对象,获取网页源码
        request = requests.get(url, headers=header)
        request.encoding = 'utf-8'
        html = request.content
        soup = BeautifulSoup(html, "lxml")
        return soup

    # 获取网页上全部文章的Abstract，返回字典对象
    def getAllArticeAbstractDirectay(self, webSourceSoup):
      # 获取网页中的所有超链接,并保存到字典
      Alllink = {}
      # 全部文献所在的div对应的class名，以列表存放，是一个soup对象
      div = webSourceSoup.select('.articleLink')
      for a in div:
        if a.text == 'Abstract':
          DOIString = a['href']  # 显示链接标签a中 href的值，类型为str,即DOI
          urlString = self.acsUrl + DOIString  # 单个文献的地址
          # 将全部文献加入到字典：key=DOI， Value=地址
          Alllink[DOIString] = urlString
      return Alllink

    # 通过每一期的文献摘要地址，找出全部文献相关内容并保存,返回文献列表，文献相关内容以字典数据保存
    '''
    返回对象：allArticlesList，全部文献内容列表，每一篇文献的内容都是一个字典数据
    '''

    def getArticeInfo(self, abstractDirectay, joural, year, issue):
      # 文献列表,文献相关内容以字典数据保存
      allArticlesList = []
      num = 0
      # 遍历字典，找出每一篇文献doi对应的地址url
      for doi, url in abstractDirectay.items():
        # 根据文献的url，加载其网页，并保存为Soup对象
        articleSoup = self.getWebSourceSoup(url)
        # 找到文献标题
        articleTitle = articleSoup.select('.articleTitle')[0].text
        # 文献作者
        writersList = []
        articleWriters = articleSoup.select('a#authors')
        for name in articleWriters:
          writersList.append(name.text)
        # 文献期巻号，页码
        articleCitation = articleSoup.select('div#citation')[0].text
        # 文献DOI
        articleDoi = doi[9:]
        # 出版时期
        pubDate = articleSoup.select('div#pubDate')[0].text
        # 摘要
        abstractText = ''
        abstract = articleSoup.select('p.articleBody_abstractText')
        if len(abstract) > 0:
          abstractText = abstract[0].text
        # 文献首图说明
        absImg = ''
        # 首图名称
        imgName = ''
        # 图片链接地址
        absImgUrl = articleSoup.select('div#absImg img')
        if len(absImgUrl) > 0:
          url = self.acsUrl + absImgUrl[0]['src']
          response = requests.get(url)
          if response.status_code == 200:
            # 图片名称
            imgName = articleDoi[8:] + '.jpg'
            path = './img/' + joural + '/' + year + '/' + issue + '/' + imgName
            # 判断是否存在，存在就跳出这一层循环，不存在就创建
            if os.path.exists(path):
              # 如果文件已存在，就结束本次循环，继续下一次
              continue
            absImg = open(path, 'wb')
            absImg.write(response.content)
            absImg.close()
            # 文献下载链接
            downloadlink = self.acsUrl + doi
            # 字典对象存放每一篇文献的数据
            articleInfomation = {
            # 文章标题: a
            '文献标题': articleTitle,
            # 作者: b
            '文献作者': writersList,
            # 文献期巻号: c
            '文献期巻号': articleCitation,
            # DOI: d
            '文献DOI': articleDoi,
            # 出版时期: e
            '出版日期': pubDate,
            # 摘要: f
            '摘要': abstractText,
            # 文献首图说明: g
            '文献配图': imgName,
            # 下载链接: h
            '文献链接': downloadlink
            }
            # 将文献数据的字典对象添加到列表并返回
            if articleInfomation not in allArticlesList:
              allArticlesList.append(articleInfomation)
            # for循环结束，该数值自增加1,即记数器功能
            num += 1
            # 显示程序进度
            total = len(abstractDirectay)
            print('爬虫已处理文献数: %d  /  总文献数：%d  (当前期/巻：%s/%s)' %
                  (num, total, year, issue))

      return allArticlesList

    # 爬虫启动
    # 两个参数
    # fromYear:起始年份
    # toYear：终止年份
    # joural期刊类别
    def startWork(self, fromYear, toYear, joural):
      # 不同期刊其网页子目录不同
      jouralMap = {
      'jacs': 'jacsat',
      'joc': 'joceah',
      'ol': 'orlef7'
      }
      # 网站URL
      jouralUrl = {
        # JACS
        'jacs' : "http://pubs.acs.org" + "/loi/jacsat/",
        # Oganic Letters
        'ol' : "http://pubs.acs.org" + "/loi/orlef7/",
        # JOC
        'joc' : "http://pubs.acs.org" + "/loi/joceah/"
      }
      # 后续可以应用 多线程 同时对多个地址进行读取数据内容
      # 取得全部 期-巻 关系
      listOFIssuesRelationDict = self.getAllVolumeDirect(jouralUrl.get(joural))
      # 第一层 循环，取出每一期数
      for year_vol, isslist  in listOFIssuesRelationDict.items():
        # 取得出版年份
        year = year_vol.split(" ")[0]
        # 对年之间的期刊进行分析采集
        if int(year) >= fromYear and int(year) <= toYear:         
          # 取得期刊数（一年一期）
          volumeNum = year_vol.split(" ")[1]
          # 按年份（期数）创建文件夹，不存在则创建，存在就跳过创建步骤
          dirpath = './img/'+ joural + '/' + year
          if not os.path.exists(dirpath):    
            os.makedirs(dirpath)
         # 取出年份中全部巻数
          for i in isslist:
            url = self.acsUrl + '/toc/' + jouralMap.get(joural) + '/' + volumeNum + '/' +  i + '/'          
            # 读取url源码soup对象
            soup = self.getWebSourceSoup(url)
            # 取得摘要字典
            abstractDirectay = self.getAllArticeAbstractDirectay(soup)
            # 创建巻号数文件夹
            issuepath = dirpath + '/' + i
            if not os.path.exists(issuepath):
              os.mkdir(issuepath)
            # 取得文献列表 [{文献标题：title, 文献DOI:doi, ...},{},{},...]
            articleList = self.getArticeInfo(abstractDirectay, joural, year, i)
            # 将文献保存到文件
            filepath = issuepath + '/' + ''
            


if __name__ == "__main__":
    # 初始化爬虫
    spider = Spider()
    # 爬虫开始工作
    spider.startWork(2016, 2016,'joc')
    

    
    


