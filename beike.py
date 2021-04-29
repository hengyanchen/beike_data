# -*- coding:utf-8 -*-
import scrapy
import parsel
from beikespider.items import BeikespiderItem
import re
import ast


buildtim = re.compile('([0-9]{4})年建成')
findyear = re.compile('单价(.*)元/平米')

class BeikeSpider(scrapy.Spider):
    name = 'beike'
    allowed_domains = ['cd.ke.com','cd.zu.ke.com']
    start_urls = ['http://cd.ke.com/xiaoqu/']

    def parse(self, response):
        '''
        解析得到大成都24个区包含的小区链接并且将地区信息传入后续解析函数
        '''

        items = BeikespiderItem()
        area_href = response.xpath('//div[@data-role="ershoufang"]/div/a')
        for i in area_href:
            area_list = ''.join(i.xpath('./text()').extract())
            url = response.urljoin(''.join(i.xpath('./@href').extract()))
            yield scrapy.Request(url,callback=self.parsexiaoqu,meta={'area_list':area_list})



    def parsexiaoqu(self,response):
        '''
        解析得到小区列表页并将每个小区的所属区域继续传入后续解析函数
        '''
        area_list = response.meta['area_list']
        totalpage = ''.join(response.xpath('//div[@class="page-box house-lst-page-box"]/@page-data').extract())
        u = ''.join(response.xpath('//div[@class="page-box house-lst-page-box"]//@page-url').extract())
        tpage = ast.literal_eval(totalpage)["totalPage"]
        for i in range(1,tpage+1):
            yield scrapy.Request(response.urljoin(u.format(page=i)),callback=self.parsexiaoqu2,meta={'area_list':area_list})


    def parsexiaoqu2(self,response):
        '''
        解析得到二手房小区部分基本信息、每条二手房房源信息链接、每条租房房源信息
        '''

        items = BeikespiderItem()
        infolist = parsel.Selector(response.text).xpath(
            '//li[@class="clear xiaoquListItem CLICKDATA"]')

        for i in infolist:

            # district = response.meta['area_list']
            xiaoqu_name = ''.join(i.xpath('.//div[@class=\'title\']/a/text()').extract())
            # bizcircle = ''.join(i.xpath('.//div[@class="positionInfo"]/a[@class="bizcircle"]/text()').extract())
            # close_subway = ''.join(i.xpath('.//div[@class="tagList"]/span/text()').extract())
            # b = ''.join(i.xpath('.//div[@class="positionInfo"]/text()').extract())
            # buildtime = ''.join(re.findall(buildtim, b))

            houseurl = ''.join(i.xpath('.//div[@class ="xiaoquListItemSellCount"]/a/@ href').extract())

            # xiaoquurl = ''.join(i.xpath('.//div[@class=\'title\']/a/@href').extract())
            # yield scrapy.Request(xiaoquurl,callback=self.parseershoufang,meta={'xiaoqu_name':xiaoqu_name,'district':district,'bizcircle':bizcircle,'close_subway':close_subway,'buildtime': buildtime,'houseurl':houseurl})
            #
            # zfurl =''.join(i.xpath('.//div[@class=\'houseInfo\']/a/@href').extract())
            # if zfurl:
            #     yield scrapy.Request(zfurl,callback=self.getzufangnextpage,meta={'xiaoqu_name':xiaoqu_name})


            x = int(''.join(i.xpath('.//div[@class ="xiaoquListItemSellCount"]/a/span/text()').extract()))
            if x != 0:
                yield  scrapy.Request(houseurl,callback=self.gethousenetpage,meta={'xiaoqu_name':xiaoqu_name})



    def parseershoufang(self,response):
        '''
        解析小区基本信息
        '''

        items = BeikespiderItem()
        xiaoquelse = parsel.Selector(response.text).xpath('//div[@class="detailHeader VIEWDATA"]')
        for i in xiaoquelse:
            items['xq_info'] = ''.join(response.xpath('//span[@class="xiaoquInfoContent"]/text()').extract()).replace(' ','').replace('\n', '').replace('\r', '')
            items['xiaoqu_name'] = response.meta['xiaoqu_name']
            items['district'] = response.meta['district']
            items['bizcircle'] = response.meta['bizcircle']
            items['close_subway'] = response.meta['close_subway']
            items['buildtime'] = response.meta['buildtime']
            items['houseurl'] = response.meta['houseurl']
            items['positioninfo'] = ''.join(i.xpath('.//div[@class="sub"]/text()').extract()).replace(' ','').replace('\n','').replace('\r','')
            items['attention'] = int(''.join(i.xpath('.//div[@class="action"]/span[@id="favCount"]/text()').extract()))
            yield items

    def getzufangnextpage(self,response):
        xiaoqu_name= response.meta['xiaoqu_name']
        urlhref = ''.join(response.xpath('//div[@class="content__pg"]/@data-url').extract())
        totalpage = ''.join(response.xpath('//div[@class="content__pg"]/@data-totalpage').extract())


        for i in range(1,int(totalpage)+1):
            url = response.urljoin(urlhref.format(page=i))
            yield scrapy.Request(url,callback=self.parsezufang,meta={'xiaoqu_name':xiaoqu_name})

    def parsezufang(self,response):
        '''
        解析租房信息
        '''
        print('租房列表')
        items = BeikespiderItem()
        zufanglist = response.xpath('//div[@class="content__list"][1]/div[@class="content__list--item"]')
        for i in zufanglist:
            items['xiaoqu_name'] = response.meta['xiaoqu_name']
            items['zufang_price'] = ''.join(i.xpath('.//span[@class="content__list--item-price"]/em/text()').extract())
            items['zufang_info'] = ''.join(i.xpath('.//p[@class="content__list--item--des"]/text()').extract()).replace('\n','').replace(' ','').replace('-','').replace(',','')
            items['zhongjie'] = ''.join(i.xpath('.//span[@class="brand"]/text()').extract()).replace(' ','').replace('\n','')
            yield items


    def gethousenetpage(self,response):
        xiaoqu_name = response.meta['xiaoqu_name']

        href = ''.join(response.xpath('//div[@class ="page-box house-lst-page-box"]/@page-url').extract())
        totalpage = ''.join(response.xpath('//div[@class ="page-box house-lst-page-box"]/@page-data').extract())
        totalpage = ast.literal_eval(totalpage)["totalPage"]
        for i in range(1,totalpage+1):

            url = response.urljoin(href.format(page=i))
            yield scrapy.Request(url, callback=self.parsehouse,meta={'xiaoqu_name':xiaoqu_name})

    def parsehouse(self, response):
        '''
        解析每一个二手房信息
        '''
        # 每个小区二手房房源列表页的小区信息，均价、季度成交量、月带看量；混杂在一起还需要正则处理

        # 每个小区二手房房源列表页
        isempty = ''.join(response.xpath('//*[@id="beike"]/div[1]/div[4]/div[1]/div[2]/div[1]/h2/span/text()').extract())
        if int(isempty)==0:
            return
        houseinfo = response.xpath('//div[@data-component="list"]//li[@class="clear"]//div[@class="address"]')
        items = BeikespiderItem()
        for i in houseinfo:
            items['xiaoqu_name'] = response.meta['xiaoqu_name']
            totalprice =  ''.join(i.xpath('.//div[@class="totalPrice"]/span/text()').extract()).replace(' ','').replace('\n','')
            if type(totalprice)== int:
                items['totalprice'] = int(totalprice)
            else:
                items['totalprice'] = float(totalprice)
            unitprice = ''.join(i.xpath('.//div[@class="unitPrice"]/span/text()').extract())
            items['unitprice'] = ''.join(re.findall(findyear,unitprice))
            items['hs_info'] = ''.join(i.xpath('.//div[@class="houseInfo"]/text()').extract()).replace(' ','').replace('\n','')
            items['follow_info'] = ''.join(i.xpath('.//div[@class="followInfo"]/text()').extract()).replace(' ','').replace('\n','')
            x = ''.join(i.xpath('.//span[@class="taxfree"]/text()').extract())
            items['trasfree'] = 1 if x == '满五年' else x==0

            yield items





