import itertools

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
            for seg2 in succinct2(m-m1, k, part+1, cur, nxt+m):
                yield (cur,) + seg1 + seg2

def main():
    #print(sorted(succinct(4,2)))
    #print(sorted(succinct2(4,2)))
    for m in range(7):
        for k in range(1,7):
            s1 = tuple(succinct_(m,k))
            s2 = tuple(sorted(succinct(m,k)))
            s3 = tuple(sorted(succinct2(m,k)))
            print(len(s1), len(s2), len(s3))
            assert s1 == s2 == s3, (m,k)
    #print(list(succinct(3,3)))

if __name__ == '__main__':
    main()
