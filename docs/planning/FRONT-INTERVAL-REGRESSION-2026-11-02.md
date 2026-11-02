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
