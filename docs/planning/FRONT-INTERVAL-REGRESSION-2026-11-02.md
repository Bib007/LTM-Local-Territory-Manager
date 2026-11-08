# Priority -1: compact street intervals and usable original fronts

Owner correction (full wording):
> Du har skrevet alle husnumre enkeltvis istedet for intervaller!!!!!!!
> husk at lave intervaller hvis den springer åbenlyse numre over fx
>
> 20-24 & 28-30
>
> og så lave en linje for lige og en for ulige... eller (lige interval) & (ulige interval) fordelt af & tegn

The attached owner screenshot stays private in Drive/local evidence. It demonstrates 1.12.6 overflowing the original footer. Use fictional test streets only.

Implementation: exact adjacent numeric/letter runs, `&` between disconnected runs, one displayed physical-front line per road/postcode/parity, combined visit counts across address types. Manual ranges retain their text. A bounded fitter protects the unchanged original footer and flags impossible lists outside the form. Stable version must be 1.12.7 so existing HA 1.12.6 installations see an update.

## 1.12.8 final clarification

Internal A/B/C/D variants do not split numeric display intervals. A missing numeric base ALWAYS splits the interval, even when the number is absent from the source (e.g. an unbuilt plot). The owner explicitly confirmed this: missing 22 gives 2–20 & 24–46 & 50–52; missing 5 gives 3 & 7–9B. If 22 is present, join to 2–46 & 50–52. Strip a starting letter and retain the final boundary suffix, such as 7–9B. Exact membership and visit counts never change. Display-only summaries work after cold reload and do not read extra geographic source data. Incomplete legacy snapshots retain their original text. Public-map privacy and original forms remain unchanged.
