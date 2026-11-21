"""The submission rules are a hard gate at the deadline, so they get real tests."""

from __future__ import annotations

import pytest

from kemp.submission import Design, build_fasta, check, load_designs, parse_fasta

SEQ = ("MKD" + "A" * 46 + "QG")[:51]  # 51 aa: base D at 3, oxy Q at 50


def ok(**overrides) -> Design:
    kwargs = {"name": "chris_01", "sequence": SEQ, "base": 3, "oxy": 50}
    return Design(**{**kwargs, **overrides})


def test_a_valid_design_has_no_problems():
    assert check([ok()]) == []


def test_catalytic_indices_are_1_based_and_typed():
    assert ok().residue(3) == "D" and ok().residue(50) == "Q"
    assert "base=2 points at K" in " ".join(check([ok(base=2)]))  # the classic off-by-one
    assert "oxy=49 points at A" in " ".join(check([ok(oxy=49)]))
    assert "outside the sequence" in " ".join(check([ok(base=999)]))
    assert "outside the sequence" in " ".join(check([ok(base=0)]))


def test_base_and_oxy_must_differ():
    seq = "D" + SEQ[1:]
    assert "same residue" in " ".join(check([Design("x", seq, base=1, oxy=1)]))


def test_histidine_cannot_be_the_donor():
    seq = SEQ[:49] + "H" + SEQ[50:]
    assert "oxy=50 points at H" in " ".join(check([Design("x", seq, base=3, oxy=50)]))


@pytest.mark.parametrize(
    "design, expected",
    [
        (ok(sequence="MKD" + "A" * 20), "must be 50-260"),
        (ok(sequence="MKD" + "A" * 300), "must be 50-260"),
        (ok(sequence=SEQ[:-1] + "X"), "not a standard uppercase amino acid"),
        (ok(sequence=SEQ.lower()), "not a standard uppercase amino acid"),
        (ok(name="bad name!"), "bad name"),
        (ok(name="x" * 65), "bad name"),
    ],
)
def test_rejected_designs(design, expected):
    assert expected in " ".join(check([design]))


def test_duplicates_and_the_20_design_cap():
    assert "duplicate name" in " ".join(check([ok(), ok(sequence="E" + SEQ[1:], base=1)]))
    assert "duplicate sequence" in " ".join(check([ok(), ok(name="chris_02")]))
    many = [ok(name=f"d{i:02d}", sequence=SEQ + "A" * i) for i in range(21)]  # unique via length
    assert "at most 20" in " ".join(check(many))
    assert check([]) == ["no designs: the file would be empty"]


def test_fasta_roundtrip_and_header_rules():
    designs = [ok(), ok(name="chris_02", sequence="E" + SEQ[1:], base=1)]
    text = build_fasta(designs)
    assert text.startswith(">chris_01 base=3 oxy=50\n")
    assert all(len(line) <= 60 for line in text.splitlines() if not line.startswith(">"))

    back, problems = parse_fasta(text)
    assert not problems
    assert [(d.name, d.sequence, d.base, d.oxy) for d in back] == [
        (d.name, d.sequence, d.base, d.oxy) for d in designs
    ]


def test_parse_accepts_synonym_and_spaces_but_not_free_text():
    designs, problems = parse_fasta(f">d1 oxyanion = 50  base=3\n{SEQ}\n")
    assert not problems and (designs[0].base, designs[0].oxy) == (3, 50)
    _, problems = parse_fasta(f">d1 base=3 oxy=50 my favourite design\n{SEQ}\n")
    assert problems and "bad header" in problems[0]
    _, problems = parse_fasta(f">d1 base=3\n{SEQ}\n")  # oxy missing
    assert problems and "bad header" in problems[0]


def test_load_designs_from_jsonl(tmp_path):
    path = tmp_path / "designs.jsonl"
    path.write_text(
        "# comment\n"
        '{"name": "chris_01", "sequence": "' + SEQ.lower() + '", "base": 3, "oxy": 50, "note": "run 1"}\n'
        "\n",
        encoding="utf-8",
    )
    designs = load_designs(path)
    assert len(designs) == 1 and designs[0].sequence == SEQ  # lowercase input is upper-cased
    assert check(designs) == []

    path.write_text('{"name": "x", "sequence": "MKD"}\n', encoding="utf-8")
    with pytest.raises(SystemExit):
        load_designs(path)
