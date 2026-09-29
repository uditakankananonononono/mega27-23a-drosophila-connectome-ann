/* C engine for the N1/N3 degree-preserving rewire: identical acceptance semantics
   to nulls.dp_rewire_fast (live hash-set membership, uniform i,j in [0,E), reject
   loops/dups, exactly n_swaps accepted swaps), deterministic via splitmix64(seed).
   RNG stream differs from numpy engines (accepted engine-swap precedent: determinism
   + documented seed, not cross-engine stream equality). Stall guard: returns early
   with accepted<n_swaps if 50M consecutive rejects (near-unrewirable group). */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static inline uint64_t sm64(uint64_t *s){ uint64_t z=(*s+=0x9E3779B97F4A7C15ULL);
  z=(z^(z>>30))*0xBF58476D1CE4E5B9ULL; z=(z^(z>>27))*0x94D049BB133111EBULL; return z^(z>>31); }

#define EMPTY UINT64_MAX

long long dp_rewire_c(long long *pre, long long *post, long long E,
                      long long n_nodes, long long n_swaps, uint64_t seed) {
    size_t cap = 1; while (cap < (size_t)(E * 2.5)) cap <<= 1;
    uint64_t *tab = (uint64_t *)malloc(cap * sizeof(uint64_t));
    if (!tab) return -1;
    for (size_t k = 0; k < cap; k++) tab[k] = EMPTY;
    size_t mask = cap - 1;
    for (long long e = 0; e < E; e++) {
        uint64_t key = (uint64_t)pre[e] * (uint64_t)n_nodes + (uint64_t)post[e];
        size_t h = (key * 0x9E3779B97F4A7C15ULL) & mask;
        while (tab[h] != EMPTY && tab[h] != key) h = (h + 1) & mask;
        tab[h] = key;
    }
    uint64_t st = seed ? seed : 0x123456789ULL;
    long long accepted = 0, stall = 0; long long stall_max = 20 * n_swaps; if (stall_max < 100000) stall_max = 100000;
    while (accepted < n_swaps && stall < stall_max) {
        long long i = (long long)(sm64(&st) % (uint64_t)E);
        long long j = (long long)(sm64(&st) % (uint64_t)E);
        if (i == j) { stall++; continue; }
        long long a = pre[i], b = post[i], c = pre[j], d = post[j];
        uint64_t n1 = (uint64_t)a * (uint64_t)n_nodes + (uint64_t)d;
        uint64_t n2 = (uint64_t)c * (uint64_t)n_nodes + (uint64_t)b;
        if (a == d || c == b || n1 == n2) { stall++; continue; }
        size_t h = (n1 * 0x9E3779B97F4A7C15ULL) & mask;
        while (tab[h] != EMPTY && tab[h] != n1) h = (h + 1) & mask;
        if (tab[h] == n1) { stall++; continue; }
        h = (n2 * 0x9E3779B97F4A7C15ULL) & mask;
        while (tab[h] != EMPTY && tab[h] != n2) h = (h + 1) & mask;
        if (tab[h] == n2) { stall++; continue; }
        /* remove old keys */
        uint64_t o1 = (uint64_t)a * (uint64_t)n_nodes + (uint64_t)b;
        uint64_t o2 = (uint64_t)c * (uint64_t)n_nodes + (uint64_t)d;
        size_t h1 = (o1 * 0x9E3779B97F4A7C15ULL) & mask;
        while (tab[h1] != o1) h1 = (h1 + 1) & mask;
        tab[h1] = EMPTY;
        size_t h2 = (o2 * 0x9E3779B97F4A7C15ULL) & mask;
        while (tab[h2] != o2) h2 = (h2 + 1) & mask;
        tab[h2] = EMPTY;
        /* NOTE: deleting from a linear-probed table breaks probe chains;
           fix by reinserting the two new keys AFTER (they are added below) and
           relying on tombstone-free deletion only being safe when the deleted
           slot does not interrupt other chains. To stay correct, use rehash-on-delete:
           walk forward from the emptied slot and reinsert displaced keys. */
        size_t k = h1;
        for (size_t nxt = (k + 1) & mask; tab[nxt] != EMPTY; nxt = (nxt + 1) & mask) {
            uint64_t kk = tab[nxt];
            size_t home = (kk * 0x9E3779B97F4A7C15ULL) & mask;
            /* if kk's home is not between h1(excluded) and nxt(included) cyclically, move it back */
            if ((home > h1 && home <= nxt) || (h1 >= nxt && (home > h1 || home <= nxt))) continue;
            tab[nxt] = EMPTY; tab[h1] = kk; h1 = nxt; k = nxt;
        }
        k = h2;
        for (size_t nxt = (k + 1) & mask; tab[nxt] != EMPTY; nxt = (nxt + 1) & mask) {
            uint64_t kk = tab[nxt];
            size_t home = (kk * 0x9E3779B97F4A7C15ULL) & mask;
            if ((home > h2 && home <= nxt) || (h2 >= nxt && (home > h2 || home <= nxt))) continue;
            tab[nxt] = EMPTY; tab[h2] = kk; h2 = nxt; k = nxt;
        }
        /* insert new keys */
        h = (n1 * 0x9E3779B97F4A7C15ULL) & mask;
        while (tab[h] != EMPTY) h = (h + 1) & mask;
        tab[h] = n1;
        h = (n2 * 0x9E3779B97F4A7C15ULL) & mask;
        while (tab[h] != EMPTY) h = (h + 1) & mask;
        tab[h] = n2;
        post[i] = d; post[j] = b;
        accepted++; stall = 0;
    }
    free(tab);
    return accepted;
}
