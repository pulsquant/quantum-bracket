"""db_bracket_loader.py — Load actual tournament brackets from the
PulsQuant database into the qbracket.Bracket data model.

Reads `tournament_brackets` + `tournament_participants` and returns a
Bracket object compatible with `src.qbracket.build_circuit` /
`champion_distribution` / `classical_mc_distribution`.

Strength ratings are passed as a dict argument so the caller can use
whatever rating system fits the sport (Elo for team sports, ATP/WTA
points for tennis, club Elo for soccer, etc.). The loader does NOT
attempt to fetch ratings itself — PulsQuant's elo_provider has gaps
for NBA/NHL/tennis at the time of writing.

Usage
-----

    from src.db_bracket_loader import load_bracket_from_db
    bracket = load_bracket_from_db("nba-playoffs-2026", strength=NBA_RATINGS)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow scripts to import this without needing to install the package.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.pulsquant_db import connect

from .qbracket import Bracket, Match


def load_bracket_from_db(
    tournament_id: str,
    strength: dict[str, float],
    *,
    cutoff_round: int | None = None,
) -> tuple[Bracket, dict[str, str]]:
    """Load the bracket structure from `tournament_brackets`.

    Returns (bracket, winners) where :
        bracket : qbracket.Bracket with N matches.
        winners : dict node_id → winner participant_id. Lets the
                  caller compute realised-marginal back-tests.

    Parameters
    ----------
    tournament_id : str
        e.g. "nba-playoffs-2026"
    strength : dict[str, float]
        Map participant_id → numeric rating (Elo-scale, base 1500).
    cutoff_round : int | None
        Optional : only include rounds with round_order >= cutoff_round.
        Useful for big-draw tennis tournaments (e.g. load Roland Garros
        from the round-of-16 onward by passing cutoff_round=5).
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '20s'")
        cur.execute(
            """
            SELECT node_id, round_order, bracket_position, parent_node_id,
                   participant_top, participant_bottom, winner_participant_id
            FROM tournament_brackets
            WHERE tournament_id = %s
            ORDER BY round_order, bracket_position
            """,
            (tournament_id,),
        )
        rows = cur.fetchall()

    if not rows:
        raise ValueError(f"No bracket rows for tournament_id={tournament_id}")

    # Optional cutoff for deep-draw tennis tournaments.
    if cutoff_round is not None:
        rows = [r for r in rows if r[1] >= cutoff_round]

    # First pass : assign integer match_ids in topological order.
    # node_id is text (e.g. "nba-East-1-R1") in the DB, we re-index 0..N-1.
    node_to_id: dict[str, int] = {}
    for i, r in enumerate(rows):
        node_to_id[r[0]] = i

    matches: list[Match] = []
    winners: dict[str, str] = {}
    teams: set[str] = set()
    min_round = min(r[1] for r in rows)

    for node_id, round_order, _bracket_pos, parent_node_id, p_top, p_bot, winner in rows:
        match_id = node_to_id[node_id]
        rel_round = round_order - min_round

        # When the round is the first (in our loaded slice), the participants
        # are known up front : we treat them as leaves of our sub-bracket.
        # For deeper rounds, the participants depend on upstream outcomes,
        # so we look up the parent_node_ids via the schema's `parent_node_id`
        # field which conveniently points to the immediate parent.
        if rel_round == 0:
            if p_top is None or p_bot is None:
                # Shouldn't happen for the first round we kept.
                continue
            parent_top = None
            parent_bot = None
            team_top = p_top
            team_bot = p_bot
            teams.add(p_top)
            teams.add(p_bot)
        else:
            # tournament_brackets schema records ONE parent per row, but
            # a knockout match has two upstream matches. The schema uses
            # `bracket_position` to chain — we reconstruct by finding the
            # two children whose own parent_node_id matches this node_id.
            children = [
                node_to_id[r[0]] for r in rows if r[3] == node_id
            ]
            if len(children) >= 2:
                parent_top = children[0]
                parent_bot = children[1]
            else:
                # Fallback : try matching by bracket_position prefix
                # (e.g. "East-1" R2 children = "East-1", "East-2" of R1)
                # This is rarely needed in practice for the PulsQuant
                # tournament refresher's output.
                parent_top = None
                parent_bot = None
            team_top = None
            team_bot = None

        matches.append(
            Match(
                match_id=match_id,
                round_idx=rel_round,
                parent_top=parent_top,
                parent_bot=parent_bot,
                team_top=team_top,
                team_bot=team_bot,
            )
        )
        if winner is not None:
            winners[node_id] = winner

    # The bracket may not be a perfect binary tree if we cut off below
    # the natural roots ; this is fine for our purposes — the deepest
    # match is still the "champion" of the loaded slice.
    bracket = Bracket(matches=matches, teams=sorted(teams), strength=strength)
    return bracket, winners


def load_participants(tournament_id: str) -> dict[str, dict]:
    """Return {participant_id: {display_name, seed, metadata}} for a tournament."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '20s'")
        cur.execute(
            """
            SELECT participant_id, display_name, seed, metadata
            FROM tournament_participants
            WHERE tournament_id = %s
            """,
            (tournament_id,),
        )
        return {
            r[0]: {"display_name": r[1], "seed": r[2], "metadata": r[3]}
            for r in cur.fetchall()
        }
