"""Neuro — the Tone Neuron desktop pet (PySide6).

Transparent, frameless, always-on-top, draggable and snaps to the nearest screen edge. Right-click
for actions: check a draft, switch the mascot language, open a culture card, get the daily review.

Run: ``python -m tone_neuron.mascot.app``. Headless verification: ``--selftest`` (Qt offscreen).
"""

from __future__ import annotations

import argparse
import os
import sys

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from tone_neuron.cards import CardBook
from tone_neuron.config import get_settings
from tone_neuron.mascot.backend_client import BackendClient, BackendUnavailable
from tone_neuron.mascot.sprites import resolve_sprite

LANGUAGES: list[tuple[str, str]] = [
    ("English (US)", "en"),
    ("English (UK)", "en-GB"),
    ("日本語 (Japanese)", "ja"),
    ("Deutsch (German)", "de"),
    ("हिन्दी (Hindi)", "hi"),
    ("中文 (Chinese)", "zh"),
    ("Português (Portuguese)", "pt"),
    ("العربية (Arabic)", "ar"),
]


class MascotWindow(QWidget):
    def __init__(self, cards: CardBook, client: BackendClient, region: str | None = None):
        super().__init__()
        self.cards = cards
        self.client = client
        self.region = (region or cards.settings.home_region).upper()
        self.state = "idle"
        self.color = "#7C9CFF"
        self._drag_offset: QPoint | None = None
        self._build_window()
        self.apply_region(self.region, announce=True)
        self.snap_to_side()

    # -- construction ------------------------------------------------------
    def _build_window(self) -> None:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(330, 264)
        self.setWindowTitle("Tone Neuron")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 16, 22, 18)
        layout.setSpacing(4)

        self.sprite_label = QLabel()
        self.sprite_label.setAlignment(Qt.AlignCenter)
        sprite_font = QFont()
        sprite_font.setPointSize(42)
        self.sprite_label.setFont(sprite_font)
        self.sprite_label.setStyleSheet("color: #E8ECFF;")

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet("color: #E8ECFF;")

        self.bubble = QLabel()
        self.bubble.setWordWrap(True)
        self.bubble.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.bubble.setStyleSheet("color: #D6DCF5; font-size: 10.5pt;")

        self.hint = QLabel("right-click for actions · drag me to an edge")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet("color: #7E88A8; font-size: 8pt;")

        layout.addWidget(self.sprite_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.bubble, 1)
        layout.addWidget(self.hint)

    # -- state -------------------------------------------------------------
    def apply_region(self, region: str, announce: bool = False) -> None:
        self.region = (region or self.region).upper()
        name = self.cards.character_name(self.region)
        self.setWindowTitle(f"Tone Neuron — {name}")
        greeting = self.cards.character(self.region).get("greeting", "")
        self.apply_state(
            "idle",
            message=greeting if announce else None,
            title=f"{name} · {self.region}" if announce else None,
        )

    def apply_state(self, state: str, message: str | None = None, title: str | None = None) -> None:
        sprite = resolve_sprite(self.cards, self.region, state)
        self.state = state
        self.color = sprite["color"]
        self.name_label.setText(sprite["name"])
        if sprite["path"]:
            pixmap = QPixmap(str(sprite["path"]))
            if not pixmap.isNull():
                self.sprite_label.setPixmap(
                    pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.sprite_label.setText("")
            else:
                self.sprite_label.setText(sprite["glyph"])
        else:
            self.sprite_label.setPixmap(QPixmap())
            self.sprite_label.setText(sprite["glyph"])
        if message is not None:
            self.bubble.setText(f"<b>{title}</b><br/>{message}" if title else message)
        self.update()

    # -- painting / dragging ----------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(2, 2, -2, -2), 24, 24)
        painter.fillPath(path, QColor(20, 24, 38, 236))
        painter.setPen(QPen(QColor(self.color), 2))
        painter.drawPath(path)
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._drag_offset is not None:
            self._drag_offset = None
            self.snap_to_side()
            event.accept()

    def snap_to_side(self) -> None:
        screen = self.screen()
        if screen is None:
            return
        area = screen.availableGeometry()
        geometry = self.frameGeometry()
        margin = 16
        center_x = geometry.center().x()
        if center_x < area.center().x():
            x = area.left() + margin
        else:
            x = area.right() - geometry.width() - margin
        y = min(max(area.top() + margin, geometry.top()), area.bottom() - geometry.height() - margin)
        self.move(x, y)

    # -- backend actions ---------------------------------------------------
    def check_draft(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self, "Check a draft", "Paste the message you are about to send:"
        )
        if ok and text.strip():
            self._run_gate(text)

    def _run_gate(self, text: str) -> None:
        try:
            result = self.client.gate(
                {
                    "text": text,
                    "context": {"surface": "email_draft"},
                    "receiver_info": {},
                    "channel": "email",
                }
            )
        except BackendUnavailable:
            self.apply_state(
                "worried",
                f"Backend unreachable at {self.client.base_url}.\n"
                "Start it with: uvicorn tone_neuron.api.main:app",
                "Offline",
            )
            return
        analysis = result.get("analysis", {}) or {}
        alert = result.get("mascot_alert", {}) or {}
        if analysis.get("region"):
            self.apply_region(analysis["region"], announce=False)
        self.apply_state(
            str(alert.get("state", "idle")),
            str(alert.get("message", "")),
            str(alert.get("title", "")),
        )

    def set_language(self, language: str) -> None:
        region = self.cards.region_for_language(language)
        if not region:
            self.apply_state("alert", f"No mascot for '{language}' yet.")
            return
        unlocked = self.cards.unlock(region)
        self.apply_region(region, announce=False)
        card = self.cards.card_for(region)
        if card:
            note = "New card unlocked!" if unlocked else "Card already collected."
            self.apply_state(
                "happy",
                f"<b>{card.region_name} · {self.cards.character_name(region)}</b><br/>"
                f"{card.greeting}<br/><i>{card.formality}</i><br/>"
                f"<span style='color:#9AA4C4'>{note}</span>",
            )

    def show_card(self) -> None:
        card = self.cards.card_for(self.region)
        if not card:
            return
        QMessageBox.information(
            self,
            f"Culture card — {card.region_name}",
            f"{card.region_name} · {card.character_name}\n"
            f"Greeting: {card.greeting}\nFormality: {card.formality}\n\n"
            f"Do:\n- " + "\n- ".join(card.dos) + "\n\nDon't:\n- " + "\n- ".join(card.donts)
            + f"\n\nTaboo topics: {', '.join(card.taboo_topics)}\n\n{card.caveat}",
        )

    def show_review(self) -> None:
        try:
            review = self.client.coaching()
        except BackendUnavailable:
            self.apply_state("worried", "Backend unreachable for the daily review.", "Offline")
            return
        themes = review.get("themes", []) or []
        theme_lines = "<br/>".join(f"• {theme.get('title')}" for theme in themes[:3])
        self.apply_state(
            "happy",
            f"{review.get('summary', '')}<br/>{theme_lines}",
            "Daily review",
        )

    # -- menu --------------------------------------------------------------
    def contextMenuEvent(self, event) -> None:  # noqa: N802 - Qt API
        menu = QMenu(self)
        menu.addAction("Check a draft…", self.check_draft)
        languages = menu.addMenu("Mascot language")
        for label, code in LANGUAGES:
            action = languages.addAction(label)
            action.triggered.connect(lambda _checked=False, code=code: self.set_language(code))
        menu.addSeparator()
        menu.addAction(f"Culture card ({self.region})", self.show_card)
        menu.addAction("Daily review", self.show_review)
        menu.addSeparator()
        menu.addAction("Quit", self.close)
        menu.exec(event.globalPos())


def selftest() -> int:
    """Construct the window and cycle every state offscreen (no display required)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(sys.argv[:1])
    cards = CardBook(get_settings())
    window = MascotWindow(cards, BackendClient(get_settings().api_base_url))
    for state in ("idle", "alert", "thinking", "happy", "worried"):
        window.apply_state(state, f"selftest {state}", "Selftest")
        app.processEvents()
    for _label, code in LANGUAGES:
        window.set_language(code)
        app.processEvents()
    window.apply_state("idle", "ready")
    window.snap_to_side()
    window.close()
    print("mascot selftest ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tone Neuron desktop mascot")
    parser.add_argument("--selftest", action="store_true", help="headless Qt self-test and exit")
    parser.add_argument("--backend", default=None, help="backend base URL")
    parser.add_argument("--language", default=None, help="mascot language code, e.g. ja")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    settings = get_settings()
    app = QApplication(sys.argv[:1])
    cards = CardBook(settings)
    window = MascotWindow(cards, BackendClient(args.backend or settings.api_base_url))
    if args.language:
        window.set_language(args.language)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
