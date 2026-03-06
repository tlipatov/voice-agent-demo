import tempfile
import unittest
from pathlib import Path

from services.rag_loader.tenant_layout import (
    SUPPORTED_INPUT_TYPES,
    collection_name_for_tenant,
    discover_tenants,
    list_supported_documents,
)


class TenantLayoutTests(unittest.TestCase):
    def test_supported_input_types(self) -> None:
        self.assertEqual(SUPPORTED_INPUT_TYPES, (".md", ".txt", ".pdf"))

    def test_collection_name_mapping(self) -> None:
        self.assertEqual(collection_name_for_tenant("silver_pine"), "silver_pine_docs")

    def test_discover_tenants_from_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "silver_pine").mkdir()
            (root / "smith_law").mkdir()
            (root / ".hidden").mkdir()
            (root / "README.md").write_text("not a tenant", encoding="utf-8")

            self.assertEqual(discover_tenants(root), ["silver_pine", "smith_law"])

    def test_list_supported_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            tenant = root / "silver_pine"
            tenant.mkdir(parents=True)
            (tenant / "faq.md").write_text("# FAQ", encoding="utf-8")
            (tenant / "hours.txt").write_text("Hours", encoding="utf-8")
            (tenant / "policy.pdf").write_text("pdf", encoding="utf-8")
            (tenant / "image.png").write_text("png", encoding="utf-8")

            docs = list_supported_documents("silver_pine", root)
            self.assertEqual([path.name for path in docs], ["faq.md", "hours.txt", "policy.pdf"])


if __name__ == "__main__":
    unittest.main()
