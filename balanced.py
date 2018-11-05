import itertools
from math import factorial as fac
binom = lambda n, k: fac(n)//fac(n-k)//fac(k)

def naiive(m,k):
    if m == 0:
        yield ()
        return
    for i in range(m*k):
        for s in naiive(m-1, k):
            if i > m*k-k:
                yield (m,)*(k-m*k+i) + s + (m,)*(m*k-i)
            else:
                yield s[:i] + (m,)*k + s[i:]

def normalize(s):
    c = sorted(set(s), key=lambda x:s.index(x))
    return tuple(c.index(x) for x in s)

def succinct_(m, k):
    return sorted(set(map(normalize, naiive(m, k))))

def succinct(m, k):
    if m == 0:
        yield (); return
    for splits in itertools.combinations_with_replacement(range(m), k-1):
        ms = [t - s for s, t in zip((0,)+splits, splits+(m-1,))]
        for segs in itertools.product(*[succinct(mm, k) for mm in ms]):
            segs = [tuple(s+x+1 for s in seg) for seg, x in zip(segs, (0,)+splits)]
            yield tuple(f for s in segs for f in (0,)+s)

def succinct2(m, k, part=0, cur=0, nxt=1):
    # Normal termination
    if m == 0 and part == 0:
        yield ()
        return
    # If we are in the sub-scheme, and we're done
    if part == k:
        # If m == 1, we have correctly used all but one of m
        if m == 1:
            yield ()
        return
    for m1 in range(m):
        for seg1 in succinct2(m1, k, 0, nxt, nxt+1):
            for seg2 in succinct2(m-m1, k, part+1, cur, nxt+m1):
                yield (cur,) + seg1 + seg2

def count(m, k):
    return binom(k*m,m)/(m*(k-1)+1)

def separate_segments(partitions):
    segments = set()
    for p in partitions:
        colors = set(p)
        for c in colors:
            segments.add(tuple(i for i,cc in enumerate(p) if c == cc))
    return segments

def main():
    print(sorted(succinct(4,2)))

    for m in range(7):
        for k in range(1,7):
            print(len(separate_segments(succinct(m,k))),)
        print()
    #print(sorted(succinct2(4,2)))
    return
    for m in range(7):
        for k in range(1,7):
            s1 = tuple(succinct_(m,k))
            s2 = tuple(sorted(succinct(m,k)))
            s3 = tuple(sorted(succinct2(m,k)))
            print(len(s1), count(k,m))
            #print(len(s1), len(s2), len(s3))
            #assert s1 == s2 == s3, (m,k)
        print()
    #print(list(succinct(3,3)))

if __name__ == '__main__':
    main()
