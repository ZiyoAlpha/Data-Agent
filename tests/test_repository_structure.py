from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_ROOT = PROJECT_ROOT / "knowledge_base" / "common"
EXPECTED_SECTIONS = {
    "metrics",
    "tables",
    "patterns",
    "contracts",
    "queries",
    "cases",
    "rules",
    "skills",
    "precedents",
}
EXPECTED_PRECEDENTS = {"fields", "schema-changes", "decisions"}


class RepositoryStructureTest(unittest.TestCase):
    def test_common_structure_is_present_and_data_free(self):
        sections = {
            path.name
            for path in COMMON_ROOT.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        precedents = {
            path.name
            for path in (COMMON_ROOT / "precedents").iterdir()
            if path.is_dir()
        }
        knowledge_files = [
            path
            for path in COMMON_ROOT.rglob("*")
            if path.is_file()
            and path.name != ".gitkeep"
            and ".dataagent" not in path.relative_to(COMMON_ROOT).parts
        ]

        self.assertEqual(sections, EXPECTED_SECTIONS)
        self.assertEqual(precedents, EXPECTED_PRECEDENTS)
        self.assertEqual(knowledge_files, [])


if __name__ == "__main__":
    unittest.main()
