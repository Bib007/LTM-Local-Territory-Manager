# Publish the fictional browser demo / udgiv webdemoen

[Dansk](DEMO-HOSTING.md)

The demo is a static browser application. It never runs the private Python/SQLite server online. Only the allowlisted demo assets are published.

## One-time GitHub setup

1. The demo pull request must first be merged into `main`, with **Demo checks** passing.
2. For the planned free public setup, make this repository public under **Settings → General → Danger Zone → Change repository visibility → Public**. Keep actual user data and credentials out of every branch and commit.
3. Open [Settings → Pages](https://github.com/Bib007/LTM-Local-Territory-Manager/settings/pages). Under **Build and deployment**, choose **Source: GitHub Actions**.
4. Open **Actions → Demo checks and Pages → Run workflow**, select `main` and run it. Later demo changes on `main` run automatically.
5. Wait for the deployment job to succeed. Open the URL shown in the deployment/Pages settings and test it in a private browser without a GitHub login.

The workflow runs checks on pull requests and private repositories but skips public deployment while the repository is private. It does not change repository visibility or enable Pages by itself.

På dansk: Gør repositoryet offentligt til den gratis løsning, vælg GitHub Actions under Pages, og kør demo-workflowet én gang. Brug først adressen som et offentligt demolink, når GitHub viser, at udgivelsen er gennemført. Det er demoen med opdigtede Bornholm-data, som bliver lagt på siden; ikke din private app eller dens databaser.

## What to verify

- No login/download needed to open the demo.
- Fictional-data notice stays visible, and Danish/English can be selected.
- An assignment/return works, and another visitor/browser has independent state.
- An IB/DNC flag removes the fictional map dot; the total card visit count stays unchanged.
- Reset removes only demo changes in that browser.
- Narrow mobile layout, map loading and print layout work on real devices.

The JavaScript model/render checks do not replace those final browser checks. OpenStreetMap tiles need internet access; respect attribution and tile-service usage policy.

## References

- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
