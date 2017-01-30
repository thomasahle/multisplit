from bs4 import BeautifulSoup
import itertools
import re
import requests
import collections
import sys
from math import factorial as fac
binom = lambda n, k: fac(n)//fac(n-k)//fac(k)
inf = 10**10



def tail(iterable):
    "Return an iterator over the last items"
    it = iter(iterable)
    try:
        next(it)
    except StopIteration:
        return []
    return it

def peek(it):
    try:
        first = next(it)
        return first, itertools.chain([first], it)
    except TypeError:
        return it[0], it

def download_ljcr():
    ''' Download the La Jolla Covering Repository sizes '''
    print('Downloading from ccrwest...', end=' ', flush=True, file=sys.stderr)
    #r = requests.get('https://www.ccrwest.org/cover/table.html').text
    r = open('jolla.htm').read()
    print('Done.', file=sys.stderr)
    soup = BeautifulSoup(r, 'html.parser')
    t = []
    for table in soup.find_all('table'):
        v = []
        for tr in tail(table.find_all('tr')):
            k = []
            for td in tail(tr.find_all('td')):
                k.append(int(td.text) if td.text.strip() else None)
            v.append(k)
        t.append(v)
    return t

def download_design(v, k, t):
    sd = simple_design(v, k, t)
    if sd is not None:
        for row in sd:
            yield row
        return
    url = 'https://www.ccrwest.org/cover/t_pages/t{}/k{}/C_{}_{}_{}.html'
    url = url.format(t, k, v, k, t)
    print('Downloading', url, file=sys.stderr)
    r = requests.get(url)
    assert r.status_code == 200, "Couldn't download design"
    soup = BeautifulSoup(r.text, 'html.parser')
    for line in soup.pre.text.strip().splitlines():
        yield [int(c) for c in line.split()]

def combine(design1, design2):
    row, design1 = peek(design1)
    v1 = len(row)
    for row1 in design1:
        for row2 in design2:
            yield row1 + [c+v1 for c in row2]

def simple_design(v, k, t):
    if t == 0: return [list(range(1, k+1))]
    if k == v: return [list(range(1, v+1))]
    if t == k: return list(itertools.combinations(range(1,v+1), k))
    if t == 1:
        res = []
        for i in range(0, v-k, k):
            res.append(list(range(i+1, i+k+1)))
        res.append(list(range(v+1-k, v+1)))
        return res

def table(ljcr, v, k, t):
    assert t <= k <= v, (v, k, t)
    assert 0 <= t
    if t == 0: return 1
    if k == v: return 1
    if t == k: return binom(v,k)
    if t == 1: return (v+k-1)//k
    assert t < len(ljcr)+2 and v < len(ljcr[t-2])
    assert v-t-1 < len(ljcr[t-2])
    assert k-t-1 < len(ljcr[t-2][v-t-1]), (v,k,t)
    res = ljcr[t-2][v-t-1][k-t-1]
    if res is None:
        return inf
    return res

def settable(ljcr, v, k, t, size):
    ljcr[t-2][v-t-1][k-t-1] = size

def simple_product(ljcr, v, k, t):
    # Decide on some v1, v2 split.
    # For each way the ts may separate, make sure we cover it.
    best = inf
    best_args = (0,())
    for v1 in range(1, v):
        sum_ = 0
        ks = []
        for t1 in range(max(0, t-v+v1), min(t, v1)+1):
            bestt = inf
            bestk = 0
            for k1 in range(max(t1, k-v+v1), min(k, v1, k-t+t1)+1):
                size = table(ljcr, v1, k1, t1) * table(ljcr, v-v1, k-k1, t-t1)
                if size < bestt:
                    bestt = size
                    bestk = k1
            sum_ += bestt
            ks.append(bestk)
        if sum_ < best:
            best = sum_
            best_args = (v1, ks)
    return best, best_args

def naur_product(ljcr, v, k, t):
    best, args = inf, (0,())
    for t1 in range(t+1):
        sum_, ks = 0, []
        # t1 <= v1 and t-t1 <= v-v1
        for v1 in range(t1, v-t+t1+1):
            best_, bestk = inf, 0
            # t1 <= k1 <= v1 and t-t1 <= k-k1 <= v-v1
            for k1 in range(max(t1, k-v+v1), min(v1, k-t+t1)+1):
                size = table(ljcr, v1, k1, t1) * table(ljcr, v-v1, k-k1, t-t1)
                if size < best_:
                    best_, bestk = size, k1
            sum_ += best_
            ks.append(bestk)
        if sum_ < best:
            best, args = sum_, (t1, ks)
    return best, args

def segment_product(ljcr, v, k, t):
    best, args = inf, (0,())
    # Also known as 's' - the segment length
    for v1 in range(1,v):
        # floor(t*v1/v) <= t1 <= ceil(t*v1/v)
        for t1 in range(t*v1//v, min(t, v1, (t*v1+v-1)//v)+1):
            best_, bestk = inf, 0
            # t1 <= k1 <= v1 and t-t1 <= k-k1 <= v-v1
            for k1 in range(max(t1, k-v+v1), min(v1, k-t+t1)+1):
                size = table(ljcr, v1, k1, t1) * table(ljcr, v-v1, k-k1, t-t1)
                if size < best_:
                    best_, bestk = size, k1
            best_ *= v
            if best_ < best:
                best, args = best_, (v1, t1, bestk)
    return best, args



def splitter(m, b, t):
    ''' Construct a list of partitions [m] -> [b], such that for any series of
        t pairwise disjoint subsets S_1, ..., S_t from [m], there is a
        partition that splits each one of S_1, ..., S_t. '''
    pass

# 1) Lav en der bruger en gammeldags splitter med segmenter af mange laengder.
# 2) Lav en der bruger roterede segmenter af samme laengde.
#    Et roteret segment af l;ngde alpha b'r d;kke en netop alpha-del af den samlede farvede m;ngde. Ja. S[ hvordan ser det ud som integers?

def search(ljcr, algo):
    matches = 0
    for t in range(2, 9):
        for v in range(len(ljcr[t-2])):
            for k in range(t+1, min(v,26)):
                tab = table(ljcr, v, k, t)
                if tab is None:
                    print('Ignoring', v, k, t, 'not in table', file=sys.stderr)
                    continue
                size, args = algo(ljcr, v, k, t)
                #size2, args2 = naur_product(ljcr, v, k, t)
                #if size < size2:
                #    print('Beat naur product for')
                #    print(v, k, t, ':', tab, size, size2)
                #print(v, k, t, ':', tab, size, end='')
                #print(args)
                #if tab == size:
                #    print(' *')
                #else: print()
                if size <= tab and tab != inf:
                    if size == tab:
                        matches += 1
                        if matches % 1 == 0:
                            print(v,k,t,'*')
                            print('Matches', matches)
                    if size < tab:
                        print(v,k,t, size, '<', tab, '!')
    print('Matches', matches)

def test(ljcr, v, k, t):
    print('table:', table(ljcr, v, k, t))
    prod, args = simple_product(ljcr, v, k, t)
    print('construct:', prod, args)
    v1, ks = args
    for t1, k1 in zip(range(max(0, t-v+v1), min(t, v1)+1), ks):
        print(
            v1, k1, t1, ':', table(ljcr, v1, k1, t1), ',',
            v-v1, k-k1, t-t1, ':', table(ljcr, v-v1, k-k1, t-t1))

def make_design(ljcr, v, k, t):
    prod, (v1, ks) = simple_product(ljcr, v, k, t)
    print('Total expected size', prod, file=sys.stderr)
    for t1, k1 in zip(range(max(0, t-v+v1), min(t, v1)+1), ks):
        print('Doing', (v1, k1, t1), (v-v1,k-k1,t-t1), file=sys.stderr)
        design1 = list(download_design(v1, k1, t1))
        design2 = list(download_design(v-v1, k-k1, t-t1))
        print('Sizes', len(design1), len(design2),
                '(', table(ljcr,v1,k1,t1), table(ljcr,v-v1,k-k1,t-t1), ')',
                file=sys.stderr)
        for row in combine(design1, design2):
            print(' '.join(map(str, row)))
            pass

def main():
    ljcr = download_ljcr()
    test(ljcr, 67, 10, 5)
    #make_design(ljcr, 67, 10, 5)
    #prod, _ = simple_product(ljcr, 67, 10, 5)
    #settable(ljcr, 67, 10, 5, prod)
    #print('Search Segment')
    #search(ljcr, segment_product)
    #print('Search Naur')
    #search(ljcr, naur_product)
    #print('Search simple')
    #search(ljcr, simple_product)


if __name__ == '__main__':
    main()

