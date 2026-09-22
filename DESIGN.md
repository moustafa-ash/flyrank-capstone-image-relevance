# Image-Relevance Engine Design

## Problem

Given a small licensed image library and blog posts, understand each image, rank relevant images by meaning, and refuse a plausible but wrong match. The demo focuses on the red-fox versus gray-wolf boundary.

## Data model

Every row is scoped to a tenant. Images have a checksum, source attribution, processing status, and one validated tag record. Posts contain editorial subject/category labels and body text. Embeddings store model, dimensions, and `REAL[]` values. Jobs, suggestions, reviews, and cost events preserve the processing trail.

## API surface

`/health`, catalog-job enqueue/status, post creation, post image ranking, suggestion inspection/review, and cost inspection. `X-Tenant-ID` scopes all `/v1` queries; `demo` is the seeded default.

## Processing flow

```text
Pexels manifest -> seed -> PostgreSQL images/posts
                         |
POST /v1/jobs/catalog -> PostgreSQL job queue -> worker
                         |
image -> Gemini structured tags -> Pydantic validation -> image_tags
caption/post text -> Gemini Embedding 2 -> embeddings
post vector x image vectors -> cosine ranking -> mismatch guard
                                                |-> suggestion/reason
                                                |-> review API
```

## Guard rules

1. Invalid or low-confidence tags are rejected and flagged.
2. A canonical subject/category mismatch is rejected with a mismatch reason.
3. Similarity below the tuned evaluation threshold is rejected.
4. If no candidate passes, return `no_confident_match` and all rejection reasons.

## Explicit non-goals

No frontend, authentication provider, model comparison, image generation, or pgvector migration is included in the required core. The linear vector scan is deliberate for the 50-image corpus.

