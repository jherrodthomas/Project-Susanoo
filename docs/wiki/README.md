# Wiki source and publication

This directory contains the **GitHub Wiki page source**. `Home.md` is the entry page and `_Sidebar.md` is the navigation sidebar. This README is not published.

## How publication works
1. Edit these pages on a feature branch and open a pull request. Link to repository files with ordinary relative links (`../../concept/CONOPS.md`) and to other pages by name (`[Lifecycle](Integrated-Lifecycle)`).
2. To show a controlled document on a page without copying it, write `<!-- include: framework/lifecycle.md -->` on its own line. The build inserts the current file.
3. CI builds the pages with [`tools/wiki/build_wiki.py`](../../tools/wiki/build_wiki.py) and fails on a missing include, a broken page link or a link to a missing file.
4. On every push to `main`, [`.github/workflows/wiki.yaml`](../../.github/workflows/wiki.yaml) rebuilds the pages and pushes them to `Project-Susanoo.wiki.git`. Each page footer names the source commit.

**One-time setup:** GitHub creates the wiki repository only after a first page has been saved from the repository's Wiki tab. Until then the publish job fails at the clone step and says so.

The wiki is a mirror. Edits made directly in the wiki are overwritten by the next merge.
