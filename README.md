# Dictionary coverage of specific Chinese individual classifiers

This project measures dictionary evidence for **individual classifier–target pairs**
in the LCMC and UCLA portions of Chinese Classifier Dataset v1.0.

The study focuses on classifier uses whose choice is lexically constrained by the
noun. Event, kind, container, standard, approximate and other non-target uses are
excluded. Highly productive individual classifiers such as `个`, `位`, `名` and `员`
are also excluded because they provide little lexical-selection information.
Polyfunctional forms are reviewed manually. A dictionary non-match is **not**
treated as a grammatical-error label.

## Main result

After manual adjudication, the core experiment contains **2,129 pair types** and
**3,801 occurrences**. The two reference works provide evidence for **26.07% of
pair types** and **46.88% of occurrences**.

The automatic scope rule alone produces a very similar result: **2,001 pair
types**, with **25.64% type coverage** and **47.13% occurrence coverage**.

The low type-level lookup rate should not be read as evidence that most corpus
pairs are incorrect. Manual inspection shows that many unmatched pairs are valid
uses involving compounds, semantic-class generalization, proper nouns or other
forms that dictionaries do not list exhaustively.

## Repository layout

| Path | Role |
|---|---|
| `main.py` | Main entry point: loads the data, applies scope decisions, performs dictionary lookup and writes outputs |
| `scope.py` | Loads and validates `classifier_scope.json` and classifies classifier forms |
| `classifier_scope.json` | Public scope definition: `include`, `exclude` and `review` |
| `prepare_data.py` | Builds `private_data/corpus.csv` from an authorized dataset copy |
| `adjudication.csv` | Manual labels for reviewed classifier–target pairs |
| `core_sample_filled.csv` | Hand-labelled sample of unmatched core pairs |
| `test_main.py` | Unit tests for the main analysis pipeline |
| `requirements-extraction.txt` | Dependency list for dictionary extraction scripts |
| `scripts/` | Scripts for rebuilding local dictionary extracts |
| `private_data/` | Prepared corpus and local dictionary extracts |
| `output/` | Generated analysis results |
| `Report.pdf` | Written project report |

## Requirements

Python **3.10 or later** is required.

The main analysis uses only the Python standard library.

Dictionary extraction requires:

```sh
pip install -r requirements-extraction.txt
```

## Run the analysis

From the repository root:

```sh
python3 main.py
```

The supplied `private_data/` directory contains the prepared corpus and local
dictionary extracts required for the analysis.

A complete run processes **11,625 valid LCMC/UCLA records** and divides them by
scope before dictionary lookup:

| Scope decision | Pair types | Occurrences |
|---|---:|---:|
| Included specific individual classifiers | 2,001 | 3,613 |
| Excluded constructions | 4,419 | 7,468 |
| Polyfunctional forms for review | 394 | 544 |
| **Total** | **6,814** | **11,625** |

Only the included specific individual classifiers form the automatic core
coverage denominator.

## Scope decisions

The project uses three operational decisions:

- `include`: lexically selective individual classifiers used in the core result;
- `exclude`: constructions outside the research question;
- `review`: polyfunctional or unlisted forms that cannot be classified safely
  from the classifier string alone.

The configuration maps the working taxonomy as follows:

| Type | Decision |
|---|---|
| Specific individual classifier | `include` |
| Highly productive individual classifier | `exclude` |
| Event classifier | `exclude` |
| Kind classifier | `exclude` |
| Container measure | `exclude` |
| Standard or approximate measure | `exclude` |
| Group-denoting expression | `exclude` |
| Ordinal, generation or time expression | `exclude` |
| Polyfunctional form | `review` |

Any classifier absent from `classifier_scope.json` defaults to `review`, so it
cannot enter the core experiment silently.

## Dictionary lookup

Two reference works are used:

- **Reference A:** 吕叔湘 Lǚ Shūxiāng (ed.), 《现代汉语八百词》 *Xiàndài
  Hànyǔ Bābǎi Cí* [*Eight Hundred Words of Modern Chinese*], classifier appendix.
  The exact local edition still requires bibliographic verification.
- **Reference B:** 刘子平 Liú Zǐpíng (2013), 《汉语量词大词典》 *Hànyǔ
  Liàngcí Dà Cídiǎn* [*A Comprehensive Dictionary of Chinese Measure Words*],
  Shanghai Lexicographical Publishing House, ISBN 9787532638567.

The prepared local files are:

- `private_data/first.csv` with `noun,classifier` pairs;
- `private_data/second.jsonl` with `classifier,entry_text,book_pages` fields.

Reference A provides exact noun–classifier evidence. Reference B is searched for
candidate evidence in examples and entry text. Because the extracted entry blocks
do not separate definitions, usage notes and examples, Reference B matches remain
**candidates**, not automatically validated pair licenses.

## Automatic core results

| Evidence status | Pair types | Occurrences |
|---|---:|---:|
| Exact Reference A pair | 164 | 812 |
| Additional Reference B example candidate | 118 | 329 |
| Additional Reference B entry-text candidate | 231 | 562 |
| Unmatched | 1,488 | 1,910 |
| **Total** | **2,001** | **3,613** |

Combined lookup evidence is found for **25.64% of automatic core pair types** and
**47.13% of occurrences**.

## Manual review

Polyfunctional forms such as `片`, `层`, `块`, `道` and `口` are reviewed at the
pair level in `adjudication.csv`.

The review routes labels as follows:

| Route | Labels | Pair types | Occurrences |
|---|---|---:|---:|
| `include` | `valid_combination` | 128 | 188 |
| `exclude` | `approx_measure_word`, `event_classifier`, `container_measure_word` | 112 | 153 |
| `drop` | target/span/marker/tokenization errors | 145 | 192 |
| `hold` | `grammatically_wrong`, `uncertain` | 9 | 11 |

`drop` is kept separate from `exclude`: some reviewed records are not valid
classifier–target relations at all, rather than valid constructions outside the
research scope.

After routing the manually accepted pairs back into the core, the adjudicated
result is **2,129 pair types / 3,801 occurrences**, with **26.07% type coverage**
and **46.88% occurrence coverage**.

## Why unmatched does not mean incorrect

A random sample of 200 unmatched automatic-core pair types was labelled by hand:

| Reason | Sample | Estimated share of unmatched types |
|---|---:|---:|
| Not a classifier–target relation | 74 | 37.0% ± 6.2 |
| Classifier not used as an individual classifier | 12 | 6.0% ± 3.1 |
| Valid use, undocumented by both references | 111 | 55.5% ± 6.4 |
| Context insufficient | 3 | 1.5% ± 1.6 |

Among the valid but undocumented cases, 56 are compounds whose head noun is
listed (50.5% ± 8.7), 51 are nouns belonging to a documented semantic class
(45.9% ± 8.6) and 4 are proper nouns or loanwords (3.6% ± 3.2). No sampled type
was an ordinary simplex noun that the references could reasonably have listed but
did not.

The first two groups are the two routes Reference A declares in its appendix as
the 以类相从 *yǐ lèi xiāng cóng* (‘grouped by class’) principle: list only the
class name, so that the classifiers suiting 树 *shù* ‘tree’ also suit 桃树, 松树;
or list one member as a representative, so that 老虎 *lǎohǔ* ‘tiger’ licenses 狮子,
豹子 by analogy (可以类推). Reference B states the same thing in every entry, which
opens with an intensional 用于 X 等 ‘used for X and the like’ before listing
examples. All 51 semantically extended sample types fall under such a statement
for their classifier; none is reached by the string lookup, which can compare
only against the examples.

The raw string-match coverage therefore mainly measures how directly dictionary
entries list the corpus pair, not whether the classifier use is linguistically
valid.

The sample is type-based rather than occurrence-based and was labelled by one
annotator, so it does not support strong per-classifier claims or inter-annotator
agreement statistics.

## Generated outputs

Running `main.py` overwrites files in `output/`:

- `pairs.csv` — included automatic-core pairs and lookup status;
- `summary.csv` — automatic core coverage counts;
- `scope_excluded.csv` — out-of-scope pairs and scope category;
- `scope_review.csv` — review pairs, manual labels and routes;
- `scope_summary.csv` — scope counts by type and occurrence;
- `run_summary.json` — reconciliation totals;
- `adjudicated_summary.csv` — coverage after manual adjudication;
- `invalid.csv` — structurally invalid input records.

The pair-level outputs reconcile to the complete valid population of **11,625
occurrences**.

## Tests and demo

Run the tests with:

```sh
python3 -m unittest discover -v
```

Run a small invented demo with:

```sh
python3 main.py --demo --output demo_output
```

The tests cover the main pipeline invariants, including scope defaults,
configuration conflicts, adjudication routing, invalid records and separation of
automatic versus adjudicated results.

## Rebuilding the corpus data

To rebuild `private_data/corpus.csv`, obtain an authorized copy of Chinese
Classifier Dataset v1.0 and run:

```sh
python3 prepare_data.py /path/to/original/data
```

The script combines `train.csv`, `dev.csv` and `test.csv`, keeps identifiers
beginning with `LCMC_` or `UCLA_`, and preserves the original split label.
The project does **not** train or evaluate a prediction model.

Dataset reference: Peinelt, Liakata and Hsieh (2017), *ClassifierGuesser*.

## Rebuilding dictionary extracts

If the source materials are available locally, rebuild the prepared dictionary
files with:

```sh
python3 scripts/export_local_reference_lexicons.py \
    --first-reference /path/to/appendix.txt \
    --second-reference-pdf /path/to/dictionary.pdf \
    --output-dir private_data
```

The extraction pipeline contains three modules:

- `lexicon.py` parses the irregular Reference A appendix;
- `dictionary_pdf.py` recovers Reference B entry blocks and printed page numbers;
- `export_local_reference_lexicons.py` runs both extractors and writes the files
  used by `main.py`.

Dictionary source files and full generated extracts should remain private unless
their distribution rights have been checked.

## Limitations

The reported percentages measure **dictionary lookup coverage**, not classifier
correctness. Unmatched pairs can result from productive compounding, semantic
class generalization, target-span problems, dictionary omissions, extraction
limitations or unusual contextual uses.

Reference B evidence is candidate-level because entry structure is not fully
recovered from the scanned dictionary. Manual labels were assigned by one
annotator in one pass.

AI tools assisted with code and documentation. I created the scope inventory,
assigned the manual labels and carried out the linguistic interpretation myself.
