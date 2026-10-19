# LTM 1.12.0-beta.50

W69 · Importér historik · S-13 / CSV medtager nu også udleveringer og forkyndernavne. En udlevering uden indleveringsdato bliver et aktivt udlån; alle indleveringer regnes som gennemgået. Gennemse navnematch, nye forkyndere, datoer, aktive udlån og konflikter før IMPORTÉR HISTORIK. Den gamle to-kolonners CSV bevares, og en ny femkolonners skabelon kan udfyldes manuelt fra scanning/foto.

Prøv med opdigtede data og en sikkerhedskopi: En indleveret og en fortsat udleveret post, både et nyt og et kendt forkyndernavn. Kontrollér udlån og gennemgang efter import og ved gentagen import. Prøv en allerede kendt gennemgang uden udlån; den skal kobles uden dobbelttælling. Overlap og uklare navne skal blokere hele importen. Prøv også aktivt udlån med ældre startdato, dansk/engelsk og mobilbredde. Original udfyldelig S-13 og LTM’s egen PDF understøttes; andre layouts/scanninger kræver manuel CSV. Main er stabil 1.11.1.
