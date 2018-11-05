import itertools
import random
from collections import Counter
import sys

# Counter-example for tree order,
# n=4, q=3, xs = 111000000111

# Counter-example for cyclic order,
# n=4, q=4, 1101000101111000

# I have checked up to n=4, q=5 and it always works with two segs per person.
# I can prove n=2 and q=2

# Conjecture:
# Alle sekvenser kan starte med range(q-1) og fuldt af en permutation af range(q)

def tree_orders(a,b):
    if a == b:
        yield ()
    for i in range(a+1, b+1):
        for o1 in tree_orders(a+1, i):
            for o2 in tree_orders(i, b):
                yield (a,) + o1 + (a,) + o2

def tree_splits_orders(n, a, b):
    if a == b:
        yield (), ()
    for i in range(a+1, b+1):
        for s1, o1 in tree_splits_orders(n, a+1, i):
            for s2, o2 in tree_splits_orders(n, i, b):
                order = (a,) + o1 + (a,) + o2
                # Do we ever need to colapse a segment?
                if not o1:
                    split = (n, 0) + s2
                    yield split, order
                else:
                    for s in range(0, n+1):
                        split = (s,) + s1 + (n-s,) + s2
                        yield split, order

def cmp(x,y):
    return x-y

def next_permutation(seq, pred=cmp):
    """Like C++ std::next_permutation() but implemented as
    generator. Yields copies of seq."""
    def reverse(seq, start, end):
        # seq = seq[:start] + reversed(seq[start:end]) + \
        #       seq[end:]
        end -= 1
        if end <= start:
            return
        while True:
            seq[start], seq[end] = seq[end], seq[start]
            if start == end or start+1 == end:
                return
            start += 1
            end -= 1
    if not seq:
        raise StopIteration
    try:
        seq[0]
    except TypeError:
        raise TypeError("seq must allow random access.")
    first = 0
    last = len(seq)
    seq = seq[:]
    # Yield input sequence as the STL version is often
    # used inside do {} while.
    yield seq
    if last == 1:
        raise StopIteration
    while True:
        next = last - 1
        while True:
            # Step 1.
            next1 = next
            next -= 1
            if pred(seq[next], seq[next1]) < 0:
                # Step 2.
                mid = last - 1
                while not (pred(seq[next], seq[mid]) < 0):
                    mid -= 1
                seq[next], seq[mid] = seq[mid], seq[next]
                # Step 3.
                reverse(seq, next1, last)
                # Change to yield references to get rid of
                # (at worst) |seq|! copy operations.
                yield seq[:]
                break
            if next == first:
                raise StopIteration
    raise StopIteration

def cumulate(xs):
    cum = [0]
    for x in xs:
        cum.append(cum[-1]+x)
    return cum

def uncum(xs):
    return tuple(x-y for x, y in zip(xs[1:], xs))

def dumb_orders(q):
    return set(itertools.permutations(list(range(q))+list(range(q-1))))

def orders(zeros, ones):
    if zeros:
        z = zeros[0]
        for order in orders(zeros[1:], (z,)+ones):
            yield (z,) + order
    for i, o in enumerate(ones):
        for order in orders(zeros, ones[:i]+ones[i+1:]):
            yield (o,) + order
    if not zeros and not ones:
        yield ()

def semi_dumb_orders(q):
    return orders(tuple(range(q)),())
    #for p in itertools.permutations(list(range(1,q))+list(range(q))):
    #    yield (0,) + p
    #for p in itertools.permutations(range(q)):
    #    if p[-1] != q-1:
    #        yield tuple(range(q-1)) + p
    #for p in cycles( tuple(range(0, q//2)) + tuple(range(q-1,q//2-1,-1))):
    #    yield tuple(range(q-1)) + p
    #yield tuple(range(q-1)) + tuple(range(0, q//2)) + tuple(range(q-1,q//2-1,-1))
    #yield tuple(range(q-1)) + tuple(range(q-1,q//2-1,-1)) + tuple(range(0, q//2))
    #for p in cycles(tuple(range(q))):
    #    yield tuple(range(q-1)) + p
    #for p in cycles(tuple(reversed(range(q)))):
        #yield tuple(range(q-1)) + p
    #for i in range(q):
    #    p = tuple(range(i)) + (q-1,) + tuple(range(i,q-1))
    #    for p2 in cycles(p):
    #        yield tuple(range(q-1)) + p2

def cycles(xs):
    for i in range(len(xs)):
        yield xs[i:] + xs[:i]

def test(xs, q, a, b, split, order):
    #ss = cumulate(split)
    ss = split
    ais, bis = [0]*q, [0]*q
    for i, c in enumerate(order):
        ais[c] += xs[ss[i]:ss[i+1]].count(0)
        bis[c] += xs[ss[i]:ss[i+1]].count(1)
    return all(a<=ai*q<a+q for ai in ais) and all(b<=bi*q<b+q for bi in bis)

# for ss in itertools.combinations_with_replacement(range(n*q+1),cuts+1):
#        ss = (0,) + ss + (n*q,)
def order_splits(order, n, q):
    its = []
    for i in range(q):
        j = order.index(i)
        if i == q-1 or j+1 == len(order) or order[j+1]==i:
            its.append([n])
        else:
            its.append(range(n+1))
    for s1s in itertools.product(*its):
        split = []
        seen = []
        for i in order:
            if i in seen:
                split.append(n-s1s[i])
            else:
                split.append(s1s[i])
                seen.append(i)
        yield cumulate(split)

def twocuts(xs, q):
    assert len(xs)%q==0
    n = len(xs)//q
    a = xs.count(0)
    b = xs.count(1)
    cuts = (q-1)*2
    for order in semi_dumb_orders(q):
    #for order in orders(tuple(range(q-1)), (q-1,)):
        good = False
        for ss in order_splits(order, n, q):
            if test(xs, q, a, b, ss, order):
                good = True
                break
        if good:
            yield order

def set_cover(sets, prev, maxsize):
    if sets and maxsize == 0:
        return
    if not sets:
        yield ()
        return
    union = sorted(set(s for se in sets for s in se))
    for x in union:
        if x <= prev:
            continue
        for cover in set_cover([s for s in sets if x not in s], x, maxsize-1):
            yield (x,) + cover

def print_smallest_covers(sets, file):
    for maxsize in range(1000):
        found_any = False
        for cover in set_cover(sets, (), maxsize):
            print(cover, file=file, end=' ')
            if is_cyclic_set(cover):
                print('C', file=file, end=' ')
            print(file=file)
            found_any = True
        if found_any:
            break

def first(it):
    try:
        return next(it)
    except StopIteration:
        return None

def is_cyclic_set(xs):
    xs = [''.join(map(str,x)) for x in xs]
    return all(x in xs[0]+xs[0] for x in xs)

# Broke cycle+single for 6/4
# [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]

TAG = sys.argv[3] if len(sys.argv) >= 4 else 'None'

def main():
    q = int(sys.argv[1])
    n = int(sys.argv[2])
    #print(list(tree_orders(0,q)))
    #print(list(orders(tuple(range(q-1)),(q,))))
    #tails = Counter()
    print('q', q, 'n', n)
    allorders = set()
    #alltails = set(itertools.permutations(range(q)))
    i = 0
    for s in next_permutation([0]*(n//2)*q+[1]*((n+1)//2*q)):
        if s[0] == 1:
            break
    #for _ in range(1000):
        i += 1
        #a = random.randrange(n+1)
        #s = [0]*(q*a) + [1]*(q*(n-a))
        #s = [0]*(n//2)*q+[1]*((n+1)//2*q)
        #random.shuffle(s)
        #s = [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1]
        #s = [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1]
        print(s, file=sys.stderr)
        res = tuple(twocuts(s,q))
        #res = first(twocuts(s,q))
        if not res:
            print(s)
            print("FEJL")
            break
        #print(res)
        #break
        allorders.add(res)
        #for tail in res:
        #    alltails.add(tail)
        #split, order = res
        #print('Order:', order)
        #print('Split:', uncum(split))
        #print('Empties:', uncum(split).count(0))
        #tails[order[q-1:]] += 1
        if TAG != 'silent' and i % 100 == 0:
            print_smallest_covers(list(allorders), file=sys.stderr)
    print_smallest_covers(list(allorders), file=sys.stdout)


if __name__ == '__main__':
    main()
