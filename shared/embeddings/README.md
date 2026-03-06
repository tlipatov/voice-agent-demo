# voice-agent-embeddings

Shared embedding utilities for `voice-agent-demo`.

## Install

From repository root:

```bash
pip install ./shared/embeddings
```

## Usage

```python
from embedding_model import embed_documents, embed_text

vector = embed_text("Hello world")
vectors = embed_documents(["doc one", "doc two"])
```
