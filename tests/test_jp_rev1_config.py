#!/usr/bin/env python3
"""Regression checks for the supported Klonoa JP Rev 1 disc/config binding."""

from __future__ import annotations

import json
import pathlib
import re
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class JapanRev1ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.game_text = (ROOT / "game.toml").read_text(encoding="utf-8")
        self.game = tomllib.loads(self.game_text)
        self.cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        self.codegen = (ROOT / "codegen_setup.c").read_text(encoding="utf-8")
        self.catalog = json.loads((ROOT / "catalog_identity.json").read_text(encoding="utf-8"))
        self.probe = json.loads((ROOT / "disc_probe.json").read_text(encoding="utf-8"))

    def test_game_identity_and_executable_header_match_jp_rev1(self) -> None:
        game = self.game["game"]
        self.assertEqual(game["id"], "SLPS-01010")
        self.assertEqual(game["exe"], "disc/SLPS_010.10")
        self.assertEqual(game["disc"], "disc/Kaze no Klonoa - Door to Phantomile (Japan) (Rev 1).cue")
        self.assertEqual(game["load_address"], "0x80011800")
        self.assertEqual(game["entry_pc"], "0x80036F18")
        self.assertEqual(game["text_size"], "0x000AD000")
        self.assertEqual(game["stack_base"], "0x801FFFF0")

    def test_prepare_disc_accepts_only_the_supplied_jp_rev1_track(self) -> None:
        prepare = self.game["prepare_disc"]
        self.assertEqual(prepare["boot_exe"], "SLPS_010.10")
        self.assertEqual(prepare["known_sizes"], [736359456])
        self.assertEqual(prepare["known_md5"], ["49ed577ac73551dd92975bc8a3fe67f2"])
        self.assertEqual(prepare["known_sha1"], ["cda51f301f2e16e74290535cff05483b641810e1"])
        self.assertNotIn("known_crc32", prepare)
        self.assertEqual(self.game["netplay"]["required_disc_fp"],
                         "61f390c189f9b6dbcbbfad502045787386247e0464fcac5e6bfeddb07bda6517")

    def test_codegen_and_runtime_build_expect_jp_generated_files(self) -> None:
        self.assertIn('GEN_MARKER "generated/SLPS_010.10_dispatch.c"', self.cmake)
        self.assertIn('GEN_FULL_GLOB "generated/SLPS_010.10_full_*.c"', self.cmake)
        self.assertIn('.gen_marker_relpath = "generated/SLPS_010.10_dispatch.c"', self.codegen)
        for text in (self.cmake, self.codegen):
            self.assertNotIn("SLUS_005.85", text)

    def test_seed_file_is_for_jp_image_and_contains_entry(self) -> None:
        seed_text = (ROOT / self.game["recompiler"]["seeds"]).read_text(encoding="utf-8")
        self.assertIn("from SLPS_010.10", seed_text.splitlines()[0])
        seeds = {line.strip().upper() for line in seed_text.splitlines() if re.fullmatch(r"0x[0-9A-Fa-f]+", line.strip())}
        self.assertIn("0X80036F18", seeds)
        self.assertEqual(len(seeds), 978)

    def test_catalog_and_probe_identify_jp_rev1(self) -> None:
        self.assertEqual(self.catalog["game"]["id"], "SLPS-01010")
        self.assertEqual(self.catalog["game"]["boot_exe"], "SLPS_010.10")
        self.assertEqual(self.catalog["marketing"]["region"], "Japan")
        self.assertEqual(self.probe["serial"], "SLPS-01010")
        self.assertEqual(self.probe["boot_exe"], "SLPS_010.10")
        self.assertEqual(self.probe["entry_pc"], "0x80036F18")
        self.assertFalse(pathlib.Path(self.probe["cue_path"]).is_absolute())

    def test_us_overlay_crc_table_is_not_reused(self) -> None:
        self.assertNotIn("overlays", self.game)
        self.assertNotIn("0xE464029F", self.game_text)


if __name__ == "__main__":
    unittest.main()
