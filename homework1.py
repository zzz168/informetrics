# -*- coding:utf-8 -*-
"""
作者: zzz
日期： 2020年10月25日
"""
import csv
import re
import datetime
import pandas as pd
import matplotlib.pyplot as plt

'''
    原始数据：博文id,用户id,用户名,博文id,是否原创,评论数,转发数,转发者id,转发者名字,转发后的博文id,转发者粉丝数,转发级别,转发内容,时间
    模型所用的数据：博文id，转发时间
    该模型作用：判断一个样本和该样本所在的样本集是否老化，并求出老化的时间点
    样本老化判断依据：取微博id不再被转发的第一天后计算转发量，转发量占总转发量90%的时间点认为是该博文老化的时间点
    样本集老化的判断依据：当某个时间点老化的样本数量占比超过90%时，则认为该时间点是样本集老化的时间点
    参考文献：Juncheng WANG,Kai YANG,Xiang LI,Mengxian ZHU.Obsolescence determination of network information based on \
            “double-proportion” method[J].Chinese Journal of Library and Information Science,2013,6(04):28-39.
'''

#读取数据文件，获取数据
def getData():
    data=[]
    with open('202008311226.csv', 'r',encoding='ISO-8859-15') as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)
    return data

#将数据按照日期倒序排序
def sortData(data):
    for i in data:
        date=datetime.datetime.strptime(i[1], "%Y/%m/%d")
        i[1]=str(date)
    sort_data=sorted(data,key=lambda x:x[1])
    return sort_data

#以一天为周期，获取周期集合
def getDateSet(sort_data):
    dates=[]
    for i in sort_data:
        date=i[1]
        dates.append(date)
    dateSet=list(set(dates))
    dateSet.sort(key=dates.index)
    return dateSet

#获取所有博文id集合
def getidSet(sort_data):
    ids=[]
    for i in sort_data:
        id=i[0]
        ids.append(id)
    idSet=list(set(ids))
    idSet.sort(key=ids.index)
    return idSet

#获取每个时间周期下微博id的集合
def getwbidAll(sort_data,dateSet):
    wbidsAll=[]            #所有时间周期下的微博id集合
    SoDsDf=pd.DataFrame(sort_data)
    grouped = dict(list(SoDsDf[0].groupby(SoDsDf[1])))
    start=0
    for date in dateSet:
        wbids = []         #某个周期下微博id的集合
        for i in range(start,start+len(grouped[date])):
            wbids.append(grouped[date][i])
        start += len(grouped[date])
        wbidsAll.append(wbids)
    return wbidsAll

#列出每条博文id被转发的时间分布，即算出在每个周期tj被转发了几次counti
def getWbidCount(idSet,wbidsAll):
    countidAll=[]
    CopycountidAll=[]     #复制countidAll，方便后续pop操作
    for id in idSet:
        countid=[]
        for wbids in wbidsAll:
            num=wbids.count(id)
            countid.append(num)
        countidAll.append(countid)
    for i in range(0,862):
        line=[]
        for j in range(0,32):
            line.append(countidAll[i][j])
        CopycountidAll.append(line)
    return countidAll,CopycountidAll

#把每条博文id总的转发次数加起来（在总的时间段中）totali
def sumcountidAll(countidAll):
    sumcountidAll=[]
    for countid in countidAll:
        sumcountidAll.append(sum(countid))
    return sumcountidAll


#遍历每个时间段，找出每条博文id没有被转发的第一个时间，记为ti,当ti前的累计转发次数除以总次数占比达到90%时则认为该博文id老化。
def getWbidObseTime(countidAll,CopycountidAll,dateSet,sumcountidAll):
    ObseTime=[]          #微博id老化对应的时间
    for i in range(0,862):
        flag = False     #判断pop出的元素是否为0
        isBbs=False      #判断该微博id是否老化
        index=0
        for j in range(0,32):
            a=countidAll[i].pop(0)  #弹出后列表改变，因此都是弹出第0个位置的值
            if a!=0:
                flag=True
                index=(CopycountidAll[i]).index(a)
            if flag and a==0:
                cnt=sum(CopycountidAll[i][0:index+1])
                if cnt/sumcountidAll[i] >= 0.9:
                    ObseTime.append(dateSet[index])
                    isBbs=True
                    break
        if isBbs==False:
            ObseTime.append('')
    return ObseTime


#统计样本集中老化的样本数量在总样本中占比，当占比达到90%时，对应的ti即样本集老化对应的时间点,返回值为每个时间点老化的样本占比
def getAllObsTime(dateSet,ObseTime):
    Obsenum=0            #微博id老化的数量
    Obsenums=[]
    flag=True            #判断样本是否开始老化
    for date in dateSet:
        Obsenum+=ObseTime.count(date)
        Obsenums.append(Obsenum/862)
        if Obsenum/862 >=0.9 and flag:
            print("样本集老化的时间： ",date)
            flag=False
    return Obsenums

if __name__ == '__main__':
    data=getData()
    sort_data=sortData(data)
    dateSet=getDateSet(sort_data)
    idset=getidSet(sort_data)
    wbidsAll=getwbidAll(sort_data,dateSet)
    countidAll, CopycountidAll=getWbidCount(idset,wbidsAll)
    sumcountidAll=sumcountidAll(countidAll)
    ObseTime=getWbidObseTime(countidAll,CopycountidAll,dateSet,sumcountidAll)
    Obsenums=getAllObsTime(dateSet,ObseTime)

    #将每个列表用数据库形式展示
    df=pd.DataFrame(sort_data,columns=["wbid","date"])
    dateSetdf=pd.DataFrame(dateSet,columns=["dateSet"])
    idsetdf=pd.DataFrame(idset,columns=["idSet"])
    countidAlldf=pd.DataFrame(CopycountidAll,columns=dateSet,index=idset)
    ObseTimedf=pd.DataFrame(ObseTime,columns=["老化时间点"],index=idset)

    #可视化展示老化时间点
    xlab=["7-6","7-7","7-8","7-9","7-10","7-11","7-12","7-13","7-14","7-15","7-16","7-17","7-18","7-19","7-20","7-21","7-22","7-23","7-24","7-25","7-26","7-27","7-28","7-29","7-30","7-31","8-1","8-2","8-3","8-4","8-5","8-6"]
    plt.figure()
    plt.plot(xlab,Obsenums)
    plt.xlabel("date")
    plt.ylabel("Proportion of Obse samples in sampleSet")
    y=[0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9]
    plt.plot(xlab,y,'k--',color='red')
    plt.annotate(r"y=0.9",xy=(0,0.9),xytext=(-1.5,+0.9),color='red')
    plt.show()


