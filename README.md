## License

This repository purposefully has no open source license. You may fork and view this repository as per GitHub's ToS but you may not copy, distribute, or modify the code in this repository.

## zephyrus

A Django/React Web App for Analyzing StarCraft II Replays.

Users can upload StarCraft II replay files and have them analyzed
to track their performance in individual matches and see trends over time.

## Functionality

Users can sign up and link as many battlenet accounts as they want to their
account. Once a battlenet account has been linked any replays associated with
that account will be fully processed and analyzed.

If a replay is not associated to any linked battlenet account it is
still stored and processed, but will not be included in trend analysis.

When replays are uploaded the original files are stored in a Google Cloud Platform (GCP) bucket
and the data from processing them is stored in the database.

## To Do

- Refactor file upload code to run file processing asynchronously

- Re-think and refactor duplicate replay verification

- Create replay list page

- Refactor code to host app on a sub-domain (app.xxx) separate from other pages

- Create replay authentication script to allow previously unauthenticated replays
to be reprocessed as authenticated ones if a battlenet account is linked after upload

- Override `all-auth`'s password reset/recovery HTML templates

- Redesign website using colour scheme of zephyrus-ladder
