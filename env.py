import json
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass
class StepResult:
    observation: Dict[str, Any]
    reward: float
    terminated: bool
    truncated: bool = False
    info: Dict[str, str] = field(default_factory=dict)
    system_prompt: Optional[str] = None


class TicTacToeEnv:
    """Tic-tac-toe where the model plays X against a seeded novice O."""

    def __init__(self) -> None:
        self.rng = random.Random()
        self.board: List[str] = [""] * 9
        self.done = False
        self.moves_used = 0
        self.outcome = "in_progress"

    def reset(self, seed: Optional[int] = None, **_: Any) -> Dict[str, Any]:
        self.rng = random.Random(seed)
        self.board = [""] * 9
        self.done = False
        self.moves_used = 0
        self.outcome = "in_progress"
        return self._observation("New game. You are X and move first.")

    def step(self, action: Any) -> StepResult:
        if self.done:
            return StepResult(
                observation=self._observation("The game is already over."),
                reward=0.0,
                terminated=True,
                info=self._terminal_info(),
            )

        cell, raw_action = self._parse_action(action)
        if cell is None:
            return self._finish(
                reward=0.0,
                outcome="invalid",
                message=f"Invalid action {raw_action!r}. Submit an empty cell index from 0 to 8.",
                extra_info={"invalid": "1.0"},
            )

        if self.board[cell] != "":
            return self._finish(
                reward=0.0,
                outcome="invalid",
                message=f"Cell {cell} is already occupied. The move is invalid.",
                extra_info={"invalid": "1.0", "attempted_cell": str(cell)},
            )

        self.board[cell] = "X"
        self.moves_used += 1

        if self._winner() == "X":
            return self._finish(1.0, "win", f"You placed X at {cell} and won.")

        if self._board_full():
            return self._finish(0.0, "draw", f"You placed X at {cell}. The game is a draw.")

        opponent_cell = self._opponent_move()
        self.board[opponent_cell] = "O"

        if self._winner() == "O":
            return self._finish(0.0, "loss", f"You placed X at {cell}. O replied at {opponent_cell} and won.")

        if self._board_full():
            return self._finish(0.0, "draw", f"You placed X at {cell}. O replied at {opponent_cell}. The game is a draw.")

        return StepResult(
            observation=self._observation(f"You placed X at {cell}. O replied at {opponent_cell}."),
            reward=0.0,
            terminated=False,
            info={
                "won": "0.0",
                "outcome": "in_progress",
                "moves_used": str(self.moves_used),
            },
        )

    def _finish(
        self,
        reward: float,
        outcome: str,
        message: str,
        extra_info: Optional[Dict[str, str]] = None,
    ) -> StepResult:
        self.done = True
        self.outcome = outcome
        info = self._terminal_info()
        if extra_info:
            info.update(extra_info)
        return StepResult(
            observation=self._observation(message),
            reward=reward,
            terminated=True,
            info=info,
        )

    def _terminal_info(self) -> Dict[str, str]:
        return {
            "won": "1.0" if self.outcome == "win" else "0.0",
            "outcome": self.outcome,
            "moves_used": str(self.moves_used),
        }

    def _observation(self, message: str) -> Dict[str, Any]:
        return {
            "message": message,
            "role": "You are X. The environment is O.",
            "board": self.board[:],
            "board_rows": [self.board[0:3], self.board[3:6], self.board[6:9]],
            "cell_indices": [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
            "valid_actions": self._valid_actions(),
            "moves_used": self.moves_used,
            "moves_remaining": max(0, 5 - self.moves_used),
        }

    def _valid_actions(self) -> List[int]:
        return [index for index, mark in enumerate(self.board) if mark == ""]

    def _winner(self) -> Optional[str]:
        for a, b, c in WIN_LINES:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    def _board_full(self) -> bool:
        return all(self.board)

    def _opponent_move(self) -> int:
        return self.rng.choice(self._valid_actions())

    def _parse_action(self, action: Any) -> Tuple[Optional[int], str]:
        if isinstance(action, dict):
            for key in ("cell", "move", "action", "index"):
                if key in action:
                    return self._parse_action(action[key])
            return None, json.dumps(action, sort_keys=True)

        if isinstance(action, int):
            return (action, str(action)) if 0 <= action <= 8 else (None, str(action))

        if isinstance(action, float) and action.is_integer():
            cell = int(action)
            return (cell, str(action)) if 0 <= cell <= 8 else (None, str(action))

        text = str(action).strip()
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            decoded = None
        if decoded is not None and decoded != text:
            return self._parse_action(decoded)

        match = re.search(r"\b([0-8])\b", text)
        if match:
            return int(match.group(1)), text
        return None, text
