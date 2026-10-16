# LTM-identitet

Den blå foldede kortmarkør og lyse/mørke ordmærker er redigerbare SVG-filer. Bevar proportionerne, og brug den udgave, som giver læsbar kontrast på baggrunden. Logoet indeholder ingen kortdata.

HA bruger `distrikt/icon.png` (128 × 128) og `distrikt/logo.png` (720 × 132). Den mørke bagplade bag ordmærket sikrer læsbar tekst i begge HA-temaer. De er eksporteret fra disse SVG-filer, ikke en ny identitet. Udviklere kan regenerere med `python scripts/build_brand_assets.py` efter installation af CairoSVG og Pillow; DejaVu Sans bruges ved PNG-eksport. Det er ikke runtime-afhængigheder. Appens `brand-logo.svg` er en kopi af `logo-dark.svg`.

HA-filkrav kontrolleret 16.10.2026: https://contributors.home-assistant.io/apps/guides/presentation/
