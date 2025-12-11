# main.py
"""
Flow:
1) Welcome -> "Verify Now" -> opens verify script in fullscreen pywebview.
2) Verify script handles Persona flow and stores result in `verify_result`.
3) MainWindow reads result, extracts name/ID/status, and shows voting page or welcome page.
4) After vote submit, prints the choice, name, and ID, then returns to welcome page.
"""
import os
import sys
import threading
import webview  # pywebview
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QMessageBox
from verify import run_verification
from crypto_utils import create_encrypted_signed_ballot


# Global handle for the pywebview window object
_pywebview_window = None
_pywebview_lock = threading.Lock()


class MainWindow(QtWidgets.QMainWindow):
    #To be dynamic
    cwd = os.path.dirname(os.path.abspath(__file__))
    print("Script path: ", cwd)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyBallot — Demo")
        self.resize(1000, 700)
        icon = os.path.join(self.cwd, "assets\\logo.png")
        self.setWindowIcon(QtGui.QIcon(icon))

        self.voter_info = None
        self.verify_result = None  # Will hold the dict returned by verify script

        # Build UI pages using QStackedLayout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        self.stack = QtWidgets.QStackedLayout(central)

        self.welcome_page = self._build_welcome_page()
        self.vote_page = self._build_vote_page()
        self.confirm_page = self._build_confirm_page()

        for p in (self.welcome_page, self.vote_page, self.confirm_page):
            self.stack.addWidget(p)

        self.stack.setCurrentWidget(self.welcome_page)

    # ---------------- UI Builders ----------------
    def _build_welcome_page(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(48, 48, 48, 48)
        v.setSpacing(24)

        # BallotID image at top
        img_label = QtWidgets.QLabel()
        banner = os.path.join(self.cwd, "assets\\MyBallot.png")
        img_label.setPixmap(QtGui.QPixmap(banner).scaledToWidth(500, QtCore.Qt.SmoothTransformation))
        img_label.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(img_label)

        # Title (left-aligned)
        title = QtWidgets.QLabel("MyKad powered balloting system")
        title.setStyleSheet("font-size:28pt; font-weight:700;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(title)

        # Subtitle / description (left-aligned)
        desc = QtWidgets.QLabel("Welcome, verify now to begin voting.")
        desc.setStyleSheet("font-size:16pt;")
        desc.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(desc)

        v.addStretch()

        # Verify Now button (centered)
        btn = QtWidgets.QPushButton("Verify Now")
        btn.setFixedHeight(64)
        btn.setFixedWidth(250)
        btn.clicked.connect(self.on_verify_now)
        btn.setStyleSheet("font-size:16pt; font-weight:600;")

        
        btn_container = QtWidgets.QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(btn)
        btn_container.addStretch()
        v.addLayout(btn_container)
        
        #COMMENT OUT 
        '''
        # ----- Skip to Voting Page button -----
        skip_btn = QtWidgets.QPushButton("Skip to Voting Page")
        skip_btn.setFixedHeight(48)
        skip_btn.setFixedWidth(250)
        skip_btn.clicked.connect(self.on_skip_to_vote)
        
        skip_layout = QtWidgets.QHBoxLayout()
        skip_layout.addStretch()
        skip_layout.addWidget(skip_btn)
        skip_layout.addStretch()
        v.addLayout(skip_layout)
        '''

        v.addStretch()
        return w

    #COMMENT OUT 
    '''
    def on_skip_to_vote(self):
        print("Skipping verification (dev mode)…")
        self.stack.setCurrentWidget(self.vote_page)
    '''
    def _build_vote_page(self):
        # Create page container
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        # Header
        header = QtWidgets.QLabel("Voting")
        header.setStyleSheet("font-size:18pt; font-weight:600;")
        v.addWidget(header)
        v.addSpacing(6)

        # Voter label
        self.voter_label = QtWidgets.QLabel("Voter: (unknown)")
        self.voter_label.setStyleSheet("font-size:12pt;")
        v.addWidget(self.voter_label)
        v.addSpacing(12)

        # Grid for 4 candidate tiles (2x2)
        grid_widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(grid_widget)
        grid.setSpacing(18)
        grid.setContentsMargins(0, 0, 0, 0)

        # Candidate button group (exclusive selection)
        self.choice_group = QtWidgets.QButtonGroup(self)
        self.choice_group.setExclusive(True)

        # Candidate definitions: (id, display_name, image_path)
        candidates = [
            (0, "Candidate A", "assets\\red.png"),
            (1, "Candidate B", "assets\\blue.png"),
            (2, "Candidate C", "assets\\green.png"),
            (3, "Candidate D", "assets\\yellow.png"),
        ]

        # We'll keep references so we can style them later
        self._candidate_buttons = {}

        for idx, (cid, name, img_path) in enumerate(candidates):
            # Tile container
            tile = QtWidgets.QWidget()
            tile_layout = QtWidgets.QVBoxLayout(tile)
            tile_layout.setContentsMargins(0, 0, 0, 0)
            tile_layout.setSpacing(8)
            tile.setMinimumSize(260, 220)

            # Big image button (checkable)
            btn = QtWidgets.QPushButton()
            btn.setCheckable(True)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.setFixedSize(260, 160)  # large clickable area
            btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    background: #fafafa;
                }
                QPushButton:checked {
                    border: 3px solid #2a7de1;
                    background: #f0f6ff;
                }
            """)
            # Try to load image; if not found, set text
            try:
                img_path = os.path.join(self.cwd, img_path)
                pix = QtGui.QPixmap(img_path)
                if not pix.isNull():
                    btn.setIcon(QtGui.QIcon(pix))
                    # icon area inside button
                    btn.setIconSize(QtCore.QSize(240, 140))
                    btn.setText("")  # prioritize icon
                else:
                    btn.setText(name)
                    btn.setStyleSheet(btn.styleSheet() + " QPushButton { font-size:14pt; }")
            except Exception:
                btn.setText(name)

            # Add to button group and keep ref
            self.choice_group.addButton(btn, cid)
            self._candidate_buttons[cid] = btn

            # Label below the image (candidate name)
            lbl = QtWidgets.QLabel(name)
            lbl.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            lbl.setStyleSheet("font-size:14pt; font-weight:600;")

            # Connect click -> handler
            btn.clicked.connect(lambda checked, i=cid: self._on_candidate_clicked(i))

            tile_layout.addWidget(btn, alignment=QtCore.Qt.AlignCenter)
            tile_layout.addWidget(lbl)
            tile_layout.addStretch()

            # Place in 2x2 grid
            row = idx // 2
            col = idx % 2
            grid.addWidget(tile, row, col)

        v.addWidget(grid_widget)

        v.addStretch()

        # Confirm button (centered)
        submit_btn = QtWidgets.QPushButton("Confirm & Submit")
        submit_btn.setFixedHeight(64)
        submit_btn.setFixedWidth(300)
        submit_btn.setStyleSheet("font-size:16pt; font-weight:700;")
        submit_btn.clicked.connect(self.on_confirm_vote)

        submit_h = QtWidgets.QHBoxLayout()
        submit_h.addStretch()
        submit_h.addWidget(submit_btn)
        submit_h.addStretch()
        v.addLayout(submit_h)

        # Keep initial style state
        self._update_candidate_styles()
        return w

    # Helper: called when a candidate tile is clicked
    def _on_candidate_clicked(self, candidate_id: int):
        # Ensure exclusivity: set checked state on the clicked button and unset others
        for cid, btn in self._candidate_buttons.items():
            btn.setChecked(cid == candidate_id)
        # update visual styles if needed
        self._update_candidate_styles()

    # Helper: refresh styles (keeps consistent visuals)
    def _update_candidate_styles(self):
        for cid, btn in self._candidate_buttons.items():
            if btn.isChecked():
                # already styled via stylesheet :checked, but you can add extra flair here
                btn.setProperty("selected", True)
            else:
                btn.setProperty("selected", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)


    def _build_confirm_page(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        lbl = QtWidgets.QLabel("Vote submitted")
        lbl.setStyleSheet("font-size:20pt; color: #1b7a3a; font-weight:700;")
        v.addWidget(lbl)
        self.confirm_info = QtWidgets.QLabel("")
        v.addWidget(self.confirm_info)
        done = QtWidgets.QPushButton("Done (Return to Welcome)")
        done.setFixedHeight(56)
        done.clicked.connect(self.on_done)
        v.addWidget(done)
        v.addStretch()
        return w

    def on_verify_now(self):

        # Run verification
        result = run_verification()
        if result.get("status") in ("completed", "approved"):
            self.voter_info = {
                "status": "approved",
                "name": result.get("name", "UNKNOWN"),
                "id_number": result.get("id_number", "UNKNOWN")
            }
            self._prepare_vote_page()
            self.stack.setCurrentWidget(self.vote_page)
        else:
            QMessageBox.warning(self, "Verification", "Verification failed or cancelled.")
            self.stack.setCurrentWidget(self.welcome_page)

    def _prepare_vote_page(self):
        name = self.voter_info.get("name", "UNKNOWN")
        idnum = self.voter_info.get("id_number", "UNKNOWN")
        masked = self._mask_id(idnum)
        self.voter_label.setText(f"Voter: {name}   ID: {masked}")
        # clear choice selection
        for b in self.choice_group.buttons():
            b.setChecked(False)

    def on_confirm_vote(self):
        checked = self.choice_group.checkedId()
        if checked == -1:
            QMessageBox.warning(self, "No selection", "Please choose a candidate.")
            return
        
        
        candidate_names = ["Candidate A", "Candidate B", "Candidate C", "Candidate D"]
        choice_text = candidate_names[checked]
        print(f"User voted: {choice_text}, Name: {self.voter_info['name']}, ID: {self.voter_info['id_number']}")
        
        #Encryption
        packet = create_encrypted_signed_ballot(self.voter_info, choice_text)
        self.confirm_info.setText(f"Ballot ID: {packet['envelope_meta']['ballot_id']}\nTime: {packet['envelope_meta']['timestamp_utc']}")
        self.stack.setCurrentWidget(self.confirm_page)


    def on_done(self):
        self.voter_info = None
        self.verify_result = None
        self.stack.setCurrentWidget(self.welcome_page)

    @staticmethod
    def _mask_id(s: str):
        if not s:
            return "UNKNOWN"
        s = str(s)
        if len(s) <= 6:
            return s[:2] + "***"
        return s[:3] + "***" + s[-2:]

    def closeEvent(self, event):
        # ensure pywebview window destroyed
        try:
            with _pywebview_lock:
                global _pywebview_window
                if _pywebview_window:
                    try:
                        webview.destroy_window(_pywebview_window)
                    except Exception:
                        pass
                    _pywebview_window = None
        except Exception:
            pass
        event.accept()


def main():
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseSoftwareOpenGL, True)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
