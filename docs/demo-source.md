# OffSight Demo Source (GitHub Pages)

This guide explains how to create a **controlled demo source** using GitHub Pages.
The idea is to host a simple HTML page that you can edit between runs to simulate
regulatory changes for the OffSight exam/demo.

## 1. Create a GitHub Pages repository

1. Create a new public repository on GitHub, for example:
   `offsight-demo-regulation`
2. Add a single file at the root of the repo called `index.html`, for example:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>OffSight Demo Regulation</title>
  </head>
  <body>
    <h1>OffSight Demo Regulation</h1>
    <p>
      Version 1 – Initial wording for the demo regulation. You can change this
      text later to simulate an update.
    </p>
  </body>
</html>
```

Commit and push this file to `main`.

## 2. Enable GitHub Pages

1. In the GitHub repo, go to **Settings → Pages**.
2. Under **Source**, select:
   - **Branch**: `main`
   - **Folder**: `/ (root)`
3. Save the settings.

GitHub will build and publish the site. After a minute or two you should see a
URL such as:

- `https://<your-username>.github.io/offsight-demo-regulation/`

You can test it by opening the URL in a browser and checking that your HTML
page loads.

## 3. Simulating “version 1 → version 2”

To simulate a regulatory change:

1. Edit `index.html` in your GitHub repo.
2. Change the body text, e.g.:

```html
<p>
  Version 2 – Updated wording for the demo regulation. This simulates an
  official guidance update that OffSight should detect.
</p>
```

3. Commit and push the change to `main`.

On the next scrape run, OffSight will:

- Fetch the updated HTML from GitHub Pages
- Extract the paragraph text
- Detect that the content hash changed
- Create a new `RegulationDocument` version
- Later, the Change Detection service will compare the two versions and create
  a `RegulationChange` with a text diff.

## 4. Using the demo source in OffSight

There are two main ways to use this demo source:

### 4.1 Via the Sources UI

1. Start the OffSight app (FastAPI + UI).
2. Open the **Sources** page (e.g. `/ui/sources`).
3. Click **Add source** and fill in:
   - **Name**: `OffSight Demo Regulation (GitHub Pages)`
   - **URL**: your GitHub Pages URL, e.g.
     `https://<your-username>.github.io/offsight-demo-regulation/`
   - **Description**: e.g. `Controlled demo regulation page hosted on GitHub Pages.`
   - **Enabled**: tick this so the scraper uses it.
4. Save the source.

### 4.2 Via the demo seeding script

OffSight also provides a demo seeding script that can upsert this source:

- Set environment variable `DEMO_SOURCE_URL` to your GitHub Pages URL, for example:

```bash
export DEMO_SOURCE_URL="https://<your-username>.github.io/offsight-demo-regulation/"
```

- Then run the seed script (see `src/offsight/core/seed_demo_sources.py` for
  details).

The seed script will:

- Create the source if it does not exist yet
- Or update the existing record if the URL already matches
- Ensure the demo source is **enabled** by default

This makes the exam/demo repeatable: you can reset the DB, re-seed, change the
GitHub Pages content from “version 1” to “version 2”, and then run the full
demo pipeline.


