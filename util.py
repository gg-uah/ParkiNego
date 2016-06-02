# -*-coding: utf-8 -*-
from datetime import datetime as dt


def mergeDict(d1, d2, func=lambda x, y: y):
    d1 = d1.copy()
    d2 = d2.copy()
    for k, v in d2.iteritems():
        d1[k] = func(d1[k], v) if k in d1 else v
    d2.update(d1)
    return d2

# warning!! only use unique value list
def swapValue(list1, list2, v1, v2):
    i = list1.index(v1)
    j = list2.index(v2)
    list2[j], list1[i] = list1[i], list2[j]
    return list1, list2

def getDate():
    return dt.now().strftime('%Y_%m_%d_%H_%M_%S')
