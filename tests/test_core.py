import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from makerworld_translator import core  # noqa: E402

FAKE = {"龙": "dragon", "灯": "lamp", "ドラゴン": "dragon", "용": "dragon", "模型": "model", "文件夹": "folder"}


def fake_translate(text, source, target):
    return FAKE.get(text, "x_" + str(len(text)))


class CoreTests(unittest.TestCase):
    def run_core(self, base, **kw):
        events = []
        params = dict(
            source=None, target_code="en", recursive=False, include_folders=False,
            dry_run=False, translate=fake_translate, emit=events.append,
        )
        params.update(kw)
        summary = core.run(base, **params)
        return summary, events

    def test_detect_source(self):
        self.assertEqual(core.detect_source("ドラゴン"), "ja")
        self.assertEqual(core.detect_source("용"), "ko")
        self.assertEqual(core.detect_source("龙灯"), "zh-CN")
        self.assertEqual(core.detect_source("हिन्दी"), "auto")

    def test_contains_script_all_asian(self):
        for sample in ["龙", "ドラゴン", "용", "สวัสดี", "हिन्दी", "العربية", "עברית", "ខ្មែរ"]:
            self.assertTrue(core.contains_script(sample, core.ALL_RANGES), sample)
        for sample in ["dragon", "Привет", "çalışma"]:
            self.assertFalse(core.contains_script(sample, core.ALL_RANGES), sample)

    def test_clean_name(self):
        self.assertEqual(core.clean_name('a<b>:c"d/e\\f|g?h*i '), "abcdefghi")
        self.assertEqual(core.clean_name("name. "), "name")
        self.assertEqual(core.clean_name("con"), "con_")
        self.assertLessEqual(len(core.clean_name("a" * 500)), core.MAX_NAME_LEN)

    def test_rename_files_keeps_extension(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ["龙.3mf", "ドラゴン.stl", "용.3mf", "plain.stl"]:
                open(os.path.join(d, n), "w").close()
            summary, _ = self.run_core(d)
            self.assertEqual(summary.renamed, 3)
            names = sorted(os.listdir(d))
            self.assertEqual(names, ["dragon (2).3mf", "dragon.3mf", "dragon.stl", "plain.stl"])

    def test_source_filter(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "龙.3mf"), "w").close()
            open(os.path.join(d, "용.3mf"), "w").close()
            korean = next(s for s in core.SOURCE_LANGUAGES if s.code == "ko")
            summary, _ = self.run_core(d, source=korean)
            self.assertEqual(summary.total, 1)
            self.assertIn("龙.3mf", os.listdir(d))

    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "龙.3mf"), "w").close()
            summary, events = self.run_core(d, dry_run=True)
            self.assertEqual(os.listdir(d), ["龙.3mf"])
            self.assertEqual(summary.renamed, 1)
            self.assertEqual(events[0].kind, "dry")

    def test_collision_never_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "dragon.3mf"), "w") as f:
                f.write("keep me")
            open(os.path.join(d, "龙.3mf"), "w").close()
            self.run_core(d)
            with open(os.path.join(d, "dragon.3mf")) as f:
                self.assertEqual(f.read(), "keep me")
            self.assertIn("dragon (2).3mf", os.listdir(d))

    def test_recursive_and_folders_bottom_up(self):
        with tempfile.TemporaryDirectory() as d:
            deep = os.path.join(d, "模型", "文件夹")
            os.makedirs(deep)
            open(os.path.join(deep, "龙.3mf"), "w").close()
            summary, _ = self.run_core(d, recursive=True, include_folders=True)
            self.assertEqual(summary.errors, 0)
            self.assertTrue(os.path.exists(os.path.join(d, "model", "folder", "dragon.3mf")))

    def test_folders_untouched_when_option_off(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "模型"))
            open(os.path.join(d, "模型", "龙.3mf"), "w").close()
            self.run_core(d, recursive=True, include_folders=False)
            self.assertTrue(os.path.exists(os.path.join(d, "模型", "dragon.3mf")))

    def test_translation_error_is_reported_not_raised(self):
        def boom(*_):
            raise RuntimeError("network down")
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "龙.3mf"), "w").close()
            summary, events = self.run_core(d, translate=boom)
            self.assertEqual(summary.errors, 1)
            self.assertEqual(events[0].kind, "error")
            self.assertEqual(os.listdir(d), ["龙.3mf"])

    def test_stop_request(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ["龙.3mf", "灯.3mf"]:
                open(os.path.join(d, n), "w").close()
            summary, _ = self.run_core(d, should_stop=lambda: True)
            self.assertTrue(summary.stopped)
            self.assertEqual(summary.renamed, 0)

    def test_nothing_to_do(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "plain.stl"), "w").close()
            summary, events = self.run_core(d)
            self.assertEqual(summary.total, 0)
            self.assertEqual(events[0].kind, "none")


if __name__ == "__main__":
    unittest.main()
