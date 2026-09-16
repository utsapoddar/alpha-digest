# Engineering Decisions

## Use one repository with two branches

The pipeline lives on `main`; generated pages live on `gh-pages`.

This keeps deployable source and generated output separate without another deployment service. The cost is a token with permission to push the publishing branch. The publisher uses a temporary clone so generated files do not dirty the workflow checkout.

## Prefer a cross-provider model chain

The pipeline previously failed when a provider changed limits or retired a model. The current chain uses two Gemini models and an NVIDIA fallback. Model names are pinned instead of using a moving alias.

This costs more configuration than a single endpoint. It prevents one provider outage from deciding whether the weekly issue exists.

## Own the retry budget

The OpenAI-compatible client has internal retries, but the pipeline disables them. `digest/summarizer.py` applies three attempts per model with explicit backoff and a 150-second request timeout.

Owning the loop makes the worst-case duration visible. The GitHub Actions timeout is 35 minutes, which covers collection plus the bounded provider chain.

## Require structured model output

The model returns JSON with a fixed top-level shape. Rendering code consumes that structure instead of parsing prose.

JSON does not guarantee factual accuracy. It does make missing fields, malformed responses, and renderer inputs easier to test.

## Render email and web output separately

Email clients and browsers have different layout constraints. Alpha Digest uses one structured summary with two templates rather than forcing one HTML document into both channels.

The tradeoff is duplicated presentation markup. The underlying facts remain shared.

## Schedule at an off-hour minute

The workflow runs at 10:17 UTC on Mondays. Scheduled GitHub Actions jobs are more likely to queue near the top of the hour, so the nonzero minute reduces avoidable scheduler contention.

## Keep subscriber data outside Git

The committed repository contains only `recipients.example.yaml`. Local addresses use an ignored file; production addresses use a GitHub Actions secret.

This prevents the public source tree from becoming a contact database.
