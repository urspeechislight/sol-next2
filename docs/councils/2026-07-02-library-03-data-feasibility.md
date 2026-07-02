# Council submission — data feasibility lens (2026-07-02)

All figures from live GETs on 2026-07-02.

Distributions: sunni-hadith-fiqh (48 works) is fully dated and volume-heavy
(46% with 5+ volumes); shia-fiqh-8th-century (941) is 37% undated with a
modern skew (C15 278, C14 147) and its top 5 authors hold only 13%; the
biography domain (2,278) is 37% undated with 1,419 authors. Era is the
strongest browse dimension over the dated two-thirds; undated is the largest
single bucket in big scopes; author is long-tail; volumes only discriminates
in hadith-style categories (in biography 80% are single-volume).

The 600 cap: five categories and every domain exceed it. Truncation made
seven of nine century counts wrong in the big category and erased 124 of 325
authors. Full fetches are cheap: 941 works in 0.25s / 404KB; 2,278 in 0.55s
/ 949KB; the whole corpus in 2.34s / 3.8MB. Verdict: page to total, drop the
cap; server aggregation unnecessary at these sizes.

Shelf feasibility: tier is effectively binary (207 primary_reference, 9,075
secondary, 51 null; primary and tertiary are empty sets). Every domain can
fill a 3-6 shelf (biography 47 … devotional 8); 11 of 39 categories have
zero and another 11 have 1-2. Hide where empty; never fall back to secondary
(any pick from 9,075 is editorial invention).

Smallest backend work: honor sort= (was silently ignored, HTTP 200 in
storage order); optionally a works-facet endpoint; remove the client cap.

Landmines: 860 author-name containment pairs ("Al-Thaalibi" beside the full
name), "Unknown Author" variants, 3,241 undated works corpus-wide (35%, but
0% in some categories), title_en missing on only 17, and 336 title+author
pairs split across multiple stems (Tadhkirat al-Fuqaha as 10 stems; the
Encyclopedia of Islamic Fiqh as 13).
