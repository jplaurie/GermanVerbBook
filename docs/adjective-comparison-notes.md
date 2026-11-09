# Comparative and superlative chapter

`grammar/comparative-and-superlative.tex` follows Cases and Declension in the
Grammar Reference. It explains the three degrees, form-building, sentence
comparisons, attributive endings, and quantity/preference words. Its reference
tables contain 60 adjectives, arranged alphabetically in two tables side by
side, including the requested tension/relaxation family. Existing verb indexes remain verb indexes.

The chapter cross-references the original adjective-ending section instead of
repeating the declension paradigms. Its German sentence examples and English
explanations are written for this book.

## Editorial choices

- Show complete `am` superlatives, and explain how the superlative stem takes
  ordinary adjective endings before a noun.
- Keep adjective comparison endings separate from case endings, using
  `ein schnelleres Auto` and `mit dem schnellsten Auto` as examples.
- Present umlaut and extra `e` as word-specific patterns, without a rule that
  would incorrectly apply them to every eligible vowel or consonant.
- Teach `als`, `so/genauso ... wie`, `weniger`, `immer`, and
  `je ... desto/umso` with explicit word-order examples.
- Keep `viel`, `wenig` and adverbial `gern(e)` in their own table.
- Explain that gradability depends on meaning and context, rather than
  declaring all participles or all absolute descriptions non-comparable.
- Include common umlaut variants of `gesund` and `nass`, with the valid
  unmodified-vowel variants explicitly noted.
- Distinguish `spannend`, `angespannt` and `entspannt` and give their complete
  comparison forms.

## References

- [Duden: comparison of German adjectives](https://www.duden.de/sprachwissen/sprachratgeber/steigerung-komparation-deutsche-adjektive)
- [Duden: als and wie in comparisons](https://www.duden.de/sprachwissen/sprachratgeber/als-oder-wie-steigerung-komparation)
- [IDS: comparison terminology](https://grammis.ids-mannheim.de/terminologie/124)
- [IDS: umlaut and changes in comparative stems](https://grammis.ids-mannheim.de/kontrastive-grammatik/3931)
- [IDS: adjective inflection](https://grammis.ids-mannheim.de/progr@mm/4067)
- [IDS: proportional clauses](https://grammis.ids-mannheim.de/kontrastive-grammatik/3790)
- [University of Michigan: German comparison forms and constructions](https://sites.lsa.umich.edu/german-resources/grammatik/komparativ/)
- [Duden: spannend](https://www.duden.de/rechtschreibung/spannend),
  [angespannt](https://www.duden.de/rechtschreibung/angespannt),
  [entspannt](https://www.duden.de/rechtschreibung/entspannt)
- [Deutsche Welle: entspannt, entspannter, am entspanntesten](https://static.dw.com/downloads/48078400/nicos-weg-a1-e13-l3-manuskript-und-wortschatz-deutsch.pdf)

- [Duden: gesund (including variants)](https://www.duden.de/rechtschreibung/gesund)
- [Duden: nass (including variants)](https://www.duden.de/rechtschreibung/nass)

## Verb correction made alongside this chapter

The existing `besichtigen` entry incorrectly used `besessen` in both its
perfect and pluperfect constructions. Both now use `besichtigt`, following
[Duden's besichtigen entry](https://www.duden.de/rechtschreibung/besichtigen).
`Besessen` remains correct for
[besitzen](https://www.duden.de/rechtschreibung/besitzen).
The incorrect forms were already present in the committed YAML; their origin
as a copying error from the neighbouring entry is an inference. A regression
test now distinguishes the two participles in both compound tenses.
