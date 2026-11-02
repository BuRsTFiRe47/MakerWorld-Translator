import os
import sys
import tempfile
import time
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


class ScriptedEngine(core.Engine):
    """Fake engine: pops one behaviour per call. A behaviour is an Exception to raise or a function."""

    def __init__(self, name, script=None, max_batch=1, max_chars=600):
        super().__init__(http=None)
        self.name, self.max_batch, self.max_chars, self.min_interval = name, max_batch, max_chars, 0
        self.script = list(script or [])
        self.calls = []

    def translate_many(self, texts, source, target):
        self.calls.append(list(texts))
        step = self.script.pop(0) if self.script else None
        if isinstance(step, Exception):
            raise step
        if callable(step):
            return step(texts)
        return [f"{self.name}:{t}" for t in texts]


def chain(*engines, **kw):
    kw.setdefault("rate_waits", (0, 0))
    kw.setdefault("final_waits", (0, 0, 0))
    kw.setdefault("delay", 0)
    return core.TranslatorChain(list(engines), **kw)


class FakeHttp:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, url, data=None, headers=None, method=None, timeout=15):
        self.requests.append((url, data, headers, method))
        return self.responses.pop(0)


class EngineParsingTests(unittest.TestCase):
    def test_google_single_and_batch(self):
        body = '[[["dragon\\n","龙\\n",null,null,10],["lamp","灯",null,null,10]],null,"zh-CN"]'
        http = FakeHttp((200, body), (200, '[[["dragon","龙",null,null,10]],null,"zh-CN"]'))
        eng = core.GoogleEngine(http)
        self.assertEqual(eng.translate_many(["龙", "灯"], "zh-CN", "en"), ["dragon", "lamp"])
        url = http.requests[0][0]
        self.assertIn("sl=zh-CN", url)
        self.assertIn("tl=en", url)
        self.assertIn("%E9%BE%99%0A%E7%81%AF", url)  # both names in ONE request, newline-joined
        self.assertEqual(eng.translate_many(["龙"], "zh-CN", "en"), ["dragon"])

    def test_google_line_count_mismatch(self):
        eng = core.GoogleEngine(FakeHttp((200, '[[["only one","龙\\n灯",null,null,10]],null,"zh-CN"]')))
        with self.assertRaises(core.BatchMismatch):
            eng.translate_many(["龙", "灯"], "zh-CN", "en")

    def test_google_rate_limit_and_errors(self):
        for status, body in [(429, "x"), (503, "x"), (200, "<html>unusual traffic from your network</html>")]:
            with self.assertRaises(core.RateLimited):
                core.GoogleEngine(FakeHttp((status, body))).translate_many(["龙"], "auto", "en")
        with self.assertRaises(RuntimeError):
            core.GoogleEngine(FakeHttp((500, "x"))).translate_many(["龙"], "auto", "en")
        with self.assertRaises(RuntimeError):
            core.GoogleEngine(FakeHttp((200, "not json"))).translate_many(["龙"], "auto", "en")

    def test_microsoft_batch_languages_and_token_refresh(self):
        reply = '[{"translations":[{"text":"dragon","to":"en"}]},{"translations":[{"text":"lamp","to":"en"}]}]'
        http = FakeHttp((200, "tok1"), (401, ""), (200, "tok2"), (200, reply))
        eng = core.MicrosoftEngine(http)
        self.assertEqual(eng.translate_many(["龙", "灯"], "zh-CN", "en"), ["dragon", "lamp"])
        api_url, data, headers, method = http.requests[-1]
        self.assertIn("from=zh-Hans", api_url)
        self.assertIn("to=en", api_url)
        self.assertEqual(method, "POST")
        self.assertEqual(headers["Authorization"], "Bearer tok2")  # refreshed after 401
        self.assertEqual(len(__import__("json").loads(data)), 2)

    def test_microsoft_auto_omits_from_and_rate_limits(self):
        http = FakeHttp((200, "tok"), (429, ""))
        eng = core.MicrosoftEngine(http)
        with self.assertRaises(core.RateLimited):
            eng.translate_many(["龙"], "auto", "en")
        self.assertNotIn("from=", http.requests[-1][0])

    def test_mymemory_parsing_and_quota(self):
        ok = core.MyMemoryEngine(FakeHttp((200, '{"responseData":{"translatedText":"dragon"},"responseStatus":200}')),
                                 email="a@b.c")
        self.assertEqual(ok.translate_many(["龙"], "zh-CN", "tr"), ["dragon"])
        self.assertIn("de=a%40b.c", ok.http.requests[0][0])
        self.assertIn("langpair=zh-CN%7Ctr", ok.http.requests[0][0])
        quota = '{"responseData":{"translatedText":"MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY"},"responseStatus":429}'
        with self.assertRaises(core.RateLimited) as cm:
            core.MyMemoryEngine(FakeHttp((200, quota))).translate_many(["龙"], "auto", "en")
        self.assertFalse(cm.exception.retry)  # daily quota: waiting is pointless


class ChainTests(unittest.TestCase):
    def test_rate_limit_waits_then_succeeds(self):
        a = ScriptedEngine("A", [core.RateLimited("429"), core.RateLimited("429")])
        c = chain(a)
        waits = []
        c.on_wait = lambda name, sec: waits.append(name)
        self.assertEqual(c.translate("龙", "zh-CN", "en"), "A:龙")
        self.assertEqual(waits, ["A", "A"])

    def test_fails_over_to_next_engine_and_stays_there(self):
        a = ScriptedEngine("A", [core.RateLimited("429")] * 10)
        b = ScriptedEngine("B")
        c = chain(a, b)
        switches = []
        c.on_switch = lambda old, new: switches.append((old, new))
        self.assertEqual(c.translate("龙", "zh-CN", "en"), "B:龙")
        self.assertEqual(c.translate("灯", "zh-CN", "en"), "B:灯")
        self.assertEqual(switches, [("A", "B")])
        self.assertEqual(len(a.calls), 3)  # first try + 2 short waits, then given up for good

    def test_non_retryable_limit_switches_immediately(self):
        a = ScriptedEngine("A", [core.RateLimited("daily quota", retry=False)])
        b = ScriptedEngine("B")
        c = chain(a, b)
        waits = []
        c.on_wait = lambda *x: waits.append(x)
        self.assertEqual(c.translate("龙", "zh-CN", "en"), "B:龙")
        self.assertEqual(waits, [])

    def test_all_engines_exhausted_is_fatal(self):
        a = ScriptedEngine("A", [core.RateLimited("429 A")] * 10)
        b = ScriptedEngine("B", [core.RateLimited("429 B")] * 10)
        with self.assertRaises(core.FatalTranslateError) as cm:
            chain(a, b).translate("龙", "zh-CN", "en")
        self.assertIn("429 B", str(cm.exception))

    def test_unreachable_engine_fails_over(self):
        a = ScriptedEngine("A", [OSError("no route to host")] * 10)
        b = ScriptedEngine("B")
        self.assertEqual(chain(a, b).translate("龙", "zh-CN", "en"), "B:龙")

    def test_ordinary_error_retries_then_raises_without_switching(self):
        a = ScriptedEngine("A", [RuntimeError("boom")] * 10)
        b = ScriptedEngine("B")
        c = chain(a, b)
        with self.assertRaises(RuntimeError):
            c.translate("龙", "zh-CN", "en")
        self.assertEqual(len(a.calls), 3)
        self.assertEqual(c.active, 0)
        self.assertEqual(b.calls, [])

    def test_batch_mismatch_falls_back_to_single_requests(self):
        a = ScriptedEngine("A", [core.BatchMismatch()], max_batch=10)
        c = chain(a)
        c.prefetch([("龙", "zh-CN"), ("灯", "zh-CN")], "en")
        self.assertEqual(a.calls, [["龙", "灯"], ["龙"], ["灯"]])
        self.assertEqual(c.translate("龙", "zh-CN", "en"), "A:龙")

    def test_prefetch_batches_groups_by_source_and_caches(self):
        a = ScriptedEngine("A", max_batch=3)
        c = chain(a)
        items = [(f"名{i}", "zh-CN") for i in range(7)] + [("ドラゴン", "ja"), ("名0", "zh-CN")]
        c.prefetch(items, "en")
        self.assertEqual([len(x) for x in a.calls], [3, 3, 1, 1])  # 7 zh in 3 requests (dup dropped) + 1 ja
        n = len(a.calls)
        self.assertEqual(c.translate("名3", "zh-CN", "en"), "A:名3")
        self.assertEqual(len(a.calls), n)  # served from the cache, no new request

    def test_prefetch_respects_char_limit_and_engine_batch_after_switch(self):
        a = ScriptedEngine("A", [core.RateLimited("x", retry=False)], max_batch=50)
        b = ScriptedEngine("B", max_batch=1)
        c = chain(a, b)
        c.prefetch([("名1", "zh-CN"), ("名2", "zh-CN"), ("名3", "zh-CN")], "en")
        self.assertEqual(b.calls, [["名1"], ["名2"], ["名3"]])  # re-split for the single-item engine

    def test_requests_are_spaced_per_engine(self):
        a = ScriptedEngine("A")
        a.min_interval = 0.1
        c = chain(a)
        start = time.monotonic()
        for t in ("龙", "灯", "模型"):
            c.translate(t, "zh-CN", "en")
        self.assertGreaterEqual(time.monotonic() - start, 0.2 - 0.02)

    def test_cancel_interrupts_long_wait(self):
        a = ScriptedEngine("A", [core.RateLimited("429")] * 10)
        c = chain(a, final_waits=(30,))
        c.on_wait = lambda *_: setattr(c, "cancelled", True)
        start = time.monotonic()
        with self.assertRaises(RuntimeError):
            c.translate("龙", "zh-CN", "en")
        self.assertLess(time.monotonic() - start, 2)

    def test_run_uses_prefetch_and_hits_few_requests(self):
        a = ScriptedEngine("A", max_batch=25)
        c = chain(a)
        with tempfile.TemporaryDirectory() as d:
            for i in range(10):
                open(os.path.join(d, f"龙{i}.3mf"), "w").close()
            summary = core.run(
                d, source=None, target_code="en", recursive=False, include_folders=False, dry_run=False,
                translate=c.translate, prefetch=lambda pairs: c.prefetch(pairs, "en"), emit=lambda e: None,
            )
            self.assertEqual(summary.renamed, 10)
            self.assertEqual(len(a.calls), 1)  # ten files, ONE request
            self.assertEqual(sorted(os.listdir(d))[0], "A:龙0.3mf".replace(":", ""))

    def test_run_aborts_cleanly_when_prefetch_is_fatal(self):
        a = ScriptedEngine("A", [core.RateLimited("429")] * 20, max_batch=25)
        c = chain(a)
        events = []
        with tempfile.TemporaryDirectory() as d:
            for n in ["龙.3mf", "灯.3mf"]:
                open(os.path.join(d, n), "w").close()
            summary = core.run(
                d, source=None, target_code="en", recursive=False, include_folders=False, dry_run=False,
                translate=c.translate, prefetch=lambda pairs: c.prefetch(pairs, "en"), emit=events.append,
            )
            self.assertTrue(summary.aborted)
            self.assertEqual(events[-1].kind, "aborted")
            self.assertEqual(sorted(os.listdir(d)), ["灯.3mf", "龙.3mf"])

    def test_job_aborts_cleanly_on_fatal_during_loop(self):
        def limited(*_):
            raise core.FatalTranslateError("429")
        with tempfile.TemporaryDirectory() as d:
            for n in ["龙.3mf", "灯.3mf"]:
                open(os.path.join(d, n), "w").close()
            events = []
            summary = core.run(
                d, source=None, target_code="en", recursive=False, include_folders=False,
                dry_run=False, translate=limited, emit=events.append,
            )
            self.assertTrue(summary.aborted)
            self.assertEqual(summary.errors, 1)

    def test_build_chain_orders(self):
        self.assertEqual([e.name for e in core.build_chain("auto").engines], ["Google", "Microsoft", "MyMemory"])
        self.assertEqual([e.name for e in core.build_chain("microsoft").engines], ["Microsoft"])
        self.assertEqual(core.build_chain("mymemory", email=" me@x.y ").engines[0].email, "me@x.y")


if __name__ == "__main__":
    unittest.main()
