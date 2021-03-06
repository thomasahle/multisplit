import collections
import itertools
import re
import sys
from math import factorial as fac

from bs4 import BeautifulSoup

import requests
import requests_cache

requests_cache.install_cache('demo_cache')

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

def download_ljcr():
    ''' Download the La Jolla Covering Repository sizes '''
    print('Downloading from ccrwest...', end=' ', flush=True, file=sys.stderr)
    #r = requests.get('https://www.ccrwest.org/cover/table.html').text
    r = open('jolla.html').read()
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
    #print('Downloading', url, file=sys.stderr)
    r = requests.get(url)
    assert r.status_code == 200, "Couldn't download design"
    soup = BeautifulSoup(r.text, 'html.parser')
    for line in soup.pre.text.strip().splitlines():
        yield [int(c) for c in line.split()]

def combine(v1, design1, design2):
    for row1 in design1:
        for row2 in design2:
            yield tuple(row1) + tuple(c+v1 for c in row2)

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
            ks.append((t1, t-t1, bestk))
        if sum_ < best:
            best = sum_
            best_args = (v1, ks)
    return best, best_args

def medium_product(ljcr, v, k, t):
    # Somewhat more advanced than the simple_product, because we can use
    # overlapping designs to sometimes save some overhead.
    best, args = inf, ()
    for v1 in range(1, v//2+2):
        # dp[i][j] = Size of design supporting up to i columns in v1 and up
        #            to j columns in v2.
        dp = [[inf]*(t+1) for _ in range(t+1)]
        dpk = [[-1]*(t+1) for _ in range(t+1)]
        dpr = [[-1]*(t+1) for _ in range(t+1)]
        for t1 in range(min(t,v1)+1):
            for t2 in range(t-t1,min(t,v-v1)+1):
                size1, k_ = min(((table(ljcr, v1, k1, t1) * table(ljcr, v-v1, k-k1, t2), k1)
                        for k1 in range(max(t1, k-v+v1), min(v1, k-t2)+1)), default=(inf,-1))
                size2, r_ = min(((dp[t1][r] + dp[t-r-1][t2], r) for r in range(t-t1,t2)), default=(inf,-1))
                if size1 < dp[t1][t2] and size1 <= size2: dpk[t1][t2] = k_
                if size2 < dp[t2][t2] and size2 <= size1: dpr[t1][t2] = r_
                dp[t1][t2] = min(dp[t1][t2], size1, size2)
        t1, t2 = min(t, v1), min(t, v-v1)
        if dp[t1][t2] < best:
            best = dp[t1][t2]
            def recover(t1,t2):
                if dpk[t1][t2] != -1:
                    return ((t1, t2, dpk[t1][t2]),)
                r = dpr[t1][t2]
                assert r != -1
                return recover(t1,r) + recover(t-r-1,t2)
            args = (v1, recover(t1,t2))
    return best, args

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
    for v1 in range(1,(v+1)//2+1):
        # floor(t*v1/v) <= t1 <= ceil(t*v1/v)
        for t1 in range(t*v1//v, min(t, v1, (t*v1+v-1)//v)+1):
            best_, bestk = inf, 0
            # t1 <= k1 <= v1 and t-t1 <= k-k1 <= v-v1
            for k1 in range(max(t1, k-v+v1), min(v1, k-t+t1)+1):
                size = table(ljcr, v1, k1, t1) * table(ljcr, v-v1, k-k1, t-t1)
                if size < best_:
                    best_, bestk = size, k1
            # When v1==v2 we can remove some redundancy
            if v1 == v-v1: best_ *= v//2
            # Unfortunately it's not clear how to do it generally
            else: best_ *= v
            if best_ < best:
                best, args = best_, (v1, t1, bestk)
    return best, args

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
                size_actual = size
                #size_actual = make_design(ljcr, v, k, t, algo, verbose=False)
                if size_actual <= tab and tab != inf:
                    if size_actual == tab:
                        matches += 1
                        if matches % 10 == 0:
                            print(v,k,t,'*')
                            print('Matches', matches)
                    if size_actual < tab:
                        print(v,k,t, size_actual, '<', tab, '!')
    print('Matches', matches)

def test(ljcr, v, k, t, algo):
    print('table:', table(ljcr, v, k, t))
    prod, args = algo(ljcr, v, k, t)
    print('construct:', prod, args)
    v1, ks = args
    for t1, t2, k1 in sorted(ks):
        print(
            v1, k1, t1, ':', table(ljcr, v1, k1, t1), ',',
            v-v1, k-k1, t2, ':', table(ljcr, v-v1, k-k1, t2))

def make_design(ljcr, v, k, t, algo, verbose=True):
    prod, (v1, ks) = algo(ljcr, v, k, t)
    if verbose:
        print('Total expected size', prod, file=sys.stderr)
    seen = set()
    for t1, t2, k1 in ks:
        if verbose:
            print('Doing', (v1, k1, t1), (v-v1,k-k1,t2), file=sys.stderr)
        design1 = list(download_design(v1, k1, t1))
        design2 = list(download_design(v-v1, k-k1, t2))
        if verbose:
            print('Sizes', len(design1), len(design2),
                    '(', table(ljcr,v1,k1,t1), table(ljcr,v-v1,k-k1,t2), ')',
                    file=sys.stderr)
        for row in combine(v1, design1, design2):
            row = tuple(sorted(row))
            if row in seen:
                if verbose:
                    print('Skipping repeated row', row, file=sys.stderr)
                continue
            seen.add(row)
            if verbose:
                print(' '.join(map(str, row)))
    if verbose:
        print('Total size was:', len(seen), file=sys.stderr)
    return len(seen)

def fun(ljcr):
    for _ in range(4):
        import random
        v = random.randrange(1, 100)
        k = random.randrange(min(v,25)+1)
        t = random.randrange(min(k,8)+1)
        test(ljcr, v, k, t, medium_product)
        test(ljcr, v, k, t, simple_product)
        print()

def main():
    ljcr = download_ljcr()
    #size_actual = make_design(ljcr, 67, 10, 5, medium_product, verbose=True)
    #print(size_actual)
    #test(ljcr, 67, 10, 5, medium_product)
    #make_design(ljcr, 5, 3, 2, medium_product)
    #prod, _ = simple_product(ljcr, 67, 10, 5)
    #settable(ljcr, 67, 10, 5, prod)
    print('Search Segment')
    search(ljcr, segment_product)
    #print('Search Naur')
    #search(ljcr, naur_product)
    #print('Search simple')
    #search(ljcr, simple_product)
    #print('Search dynamic programming')
    #search(ljcr, medium_product)


if __name__ == '__main__':
    main()
