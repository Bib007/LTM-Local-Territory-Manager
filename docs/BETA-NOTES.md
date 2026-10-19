# LTM 1.12.0-beta.42

Ét ønskepunkt: W64 · Ændringslog ved HA-opdatering.

- Home Assistant fik en ændringslog, der var stoppet ved beta.29. Appmappens ændringslog følger nu projektets fulde versionshistorik, inklusive beta.30–42.
- En ny pakkekontrol stopper udgivelsen, hvis de to ændringslogfiler afviger, eller den aktuelle version ikke står øverst. Kontrollen gælder både den komplette programpakke og HA-betaen.
- Tidligere udgivelsespakker/tags og lokale data ændres ikke. API-hentning og login er uændrede.

Prøv i Home Assistant: Søg efter opdateringer til Distrikt Beta, og åbn ændringsloggen før opdatering. Den skal begynde med 1.12.0-beta.42 og også vise beta.41, beta.40 og de tidligere noter. Kontrollér efter opdatering, at appen viser beta.42. Hvis HA stadig viser den gamle liste, opdatér først repositoryoplysningerne og genindlæs appsiden. Visning på egen HA er et ejertrin; pakning og kanal kontrolleres automatisk. Main er stabil 1.11.1.
