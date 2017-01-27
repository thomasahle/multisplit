from bs4 import BeautifulSoup
import re
import requests
import collections
import numpy as np

def tail(iterable):
    "Return an iterator over the last items"
    it = iter(iterable)
    try:
        next(it)
    except StopIteration:
        return []
    return it

def download_ljcr():
    ''' Download the La Jolla Covering Repository sizes '''
    print('Downloading from ccrwest...', end=' ', flush=True)
    #r = requests.get('https://www.ccrwest.org/cover/table.html').text
    r = open('jolla.htm').read()
    print('Done.')
    soup = BeautifulSoup(r, 'html.parser')
    t = []
    for table in soup.find_all('table'):
        v = []
        for tr in tail(table.find_all('tr')):
            k = []
            for td in tr.find_all('a'):
                k.append(int(td.text) if td.text.strip() else None)
            v.append(k)
        t.append(v)
    return t

def table(ljcr, t, k, v):
    assert 2 <= t <= 8
    assert t+1 <= k <= v+1
    assert v < len(ljcr[t-2])
    return ljcr[t-2][v-t-1][k-t-1]

def splitter(m, b, t):
    ''' Construct a list of partitions [m] -> [b], such that for any series of
        t pairwise disjoint subsets S_1, ..., S_t from [m], there is a
        partition that splits each one of S_1, ..., S_t. '''
    pass

def main():
    ljcr = download_ljcr()
    print(np.array(ljcr[0]))
    print(table(ljcr, 2, 3, 4))
    print(table(ljcr, 2, 3, 5))
    print(table(ljcr, 2, 4, 5))

if __name__ == '__main__':
    main()

