import sys
import re
import logging
import genanki
from typing import Generator, List, Any
from enum import Enum
from functools import lru_cache
import requests

import requests_cache
requests_cache.install_cache('dutch-words', backend='sqlite')

from anki_decks.common import jinja_env, css

from wiktionaryparser import WiktionaryParser


class DeOfHet(Enum):
    DE = "de"
    HET = "het"
    UNKNOWN = "unknown"


def de_of_het(word):
    response = requests.get(f"https://www.welklidwoord.nl/{word}")
    data = response.text
    de = re.search("<span>De</span>", data, re.IGNORECASE)
    if de:
        return DeOfHet.DE
    het = re.search("<span>Het</span>", data, re.IGNORECASE)
    if het:
        return DeOfHet.HET
    return DeOfHet.UNKNOWN


jinja_env.globals.update(de_of_het=de_of_het)
template = jinja_env.get_template("dutch-words-back.html")
dutch_deck = genanki.Deck(79475942179, "Dutch Words")


class DutchNote(genanki.Note):
    @property
    def guid(self):
        return genanki.guid_for(self.fields[0], self.fields[1])


class DutchWords:
    model_id = 7491739751
    parser = None

    def get_parser(self):
        if not self.parser:
            self.parser = WiktionaryParser()
        return self.parser

    def get_model(self):
        return genanki.Model(
            self.model_id,
            "Dutch Word",
            css=css,
            fields=[
                {"name": "Word"},
                {"name": "Part of speech"},
                {"name": "Question"},
                {"name": "Answer"},
            ],
            templates=[
                {
                    "name": "Dutch card",
                    "qfmt": "<h1><center>{{Question}}</center></h1>",
                    "afmt": "{{Answer}}",
                },
            ],
        )

    def get_word(self, query: str) -> List[Any]:
        entries = self.get_parser().fetch(query, "dutch")
        return entries

    def get_back_templates(
        self, entries: List[Any], original_word: str, note: str
    ) -> Generator[str, None, None]:
        for entry in entries:
            yield self.get_back_template_for_entry(entry, original_word, note)

    def get_back_template_for_entry(
        self, entry: str, original_word: str, note: str
    ) -> str:
        definitions = entry["definitions"]
        if not definitions:
            logging.warn(f"No definition found for {original_word}")
        pronunciations = entry["pronunciations"]
        return template.render(
            definitions=definitions,
            pronunciations=pronunciations,
            word=original_word,
            note=note,
        )

    def add_word_to_deck(self, word: str, note: str = "") -> None:
        entries = self.get_word(word)
        for index, tmpl_str in enumerate(self.get_back_templates(entries, word, note)):
            note = DutchNote(
                model=self.get_model(), fields=[word, f"entry-{index}", word, tmpl_str]
            )
            dutch_deck.add_note(note)

    def read_file(self, file_name: str):
        with open(file_name) as f:
            lines = f.readlines()
            for line in lines[:50]:
                word, note = line.split(";")
                word = re.sub("\([^ ]*\)", "", word)
                self.add_word_to_deck(word, note)
        genanki.Package(dutch_deck).write_to_file("dutch_deck.apkg")
