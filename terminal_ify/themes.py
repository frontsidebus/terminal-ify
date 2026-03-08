"""Spotify-inspired dark theme CSS for terminal-ify."""

TERMINAL_IFY_CSS = """
/* ============================================================
   terminal-ify Theme
   A dark Spotify-inspired design for Textual TUI
   ============================================================ */

/* ---- Screen ---- */
Screen {
    background: #121212;
    color: #FFFFFF;
}

/* ---- Header ---- */
#header {
    dock: top;
    height: auto;
    background: #181818;
    color: #FFFFFF;
    padding: 1 2;
    border-bottom: solid #1DB954;
}

#header .app-title {
    text-style: bold;
    color: #1DB954;
}

#header .app-subtitle {
    color: #B3B3B3;
}

/* ---- Sidebar / Navigation ---- */
#sidebar {
    dock: left;
    width: 25;
    background: #000000;
    border-right: solid #181818;
    padding: 1 0;
}

#sidebar .nav-section-title {
    color: #727272;
    text-style: bold;
    padding: 1 2 0 2;

}

.nav-item {
    padding: 0 2;
    height: 3;
    color: #B3B3B3;
    content-align-vertical: middle;
}

.nav-item:hover {
    color: #FFFFFF;
    background: #282828;
}

.nav-item:focus {
    color: #FFFFFF;
    background: #282828;
}

.nav-item.--active {
    color: #1DB954;
    text-style: bold;
}

.nav-item.--active:hover {
    color: #1ed760;
}

/* ---- Content Area ---- */
#content {
    background: #121212;
    padding: 1 2;
    overflow-y: auto;
}

#content-header {
    height: auto;
    padding: 1 0;
    margin-bottom: 1;
}

#content-header .page-title {
    text-style: bold;
    color: #FFFFFF;
}

#content-header .page-subtitle {
    color: #B3B3B3;
}

/* ---- Now Playing Bar ---- */
#now-playing-bar {
    dock: bottom;
    height: 5;
    background: #181818;
    border-top: solid #1DB954;
    layout: horizontal;
    padding: 0 2;
}

#now-playing-bar #np-track-info {
    width: 1fr;
    height: 100%;
    content-align-vertical: middle;
    padding: 1 0;
}

#now-playing-bar #np-track-info .track-title {
    color: #FFFFFF;
    text-style: bold;
}

#now-playing-bar #np-track-info .track-artist {
    color: #B3B3B3;
}

#now-playing-bar #np-track-info .track-artist:hover {
    color: #FFFFFF;
    text-style: underline;
}

#now-playing-bar #np-controls {
    width: 2fr;
    height: 100%;
    content-align: center middle;
    padding: 1 0;
}

#now-playing-bar #np-controls .control-btn {
    min-width: 3;
    color: #B3B3B3;
    background: transparent;
    border: none;
    padding: 0 1;
}

#now-playing-bar #np-controls .control-btn:hover {
    color: #FFFFFF;
}

#now-playing-bar #np-controls .control-btn.--active {
    color: #1DB954;
}

#now-playing-bar #np-controls .control-btn.--active:hover {
    color: #1ed760;
}

#now-playing-bar #np-controls .play-btn {
    color: #FFFFFF;
    text-style: bold;
    min-width: 5;
}

#now-playing-bar #np-controls .play-btn:hover {
    color: #1DB954;
}

#now-playing-bar #np-volume {
    width: 1fr;
    height: 100%;
    content-align: right middle;
    padding: 1 0;
}

#np-progress-row {
    height: 1;
    width: 100%;
    layout: horizontal;
}

#np-progress-row .time-label {
    width: 5;
    color: #727272;
    content-align: center middle;
}

/* ---- Progress Bar ---- */
.progress-bar {
    height: 1;
    background: #535353;
    width: 1fr;
}

.progress-bar > .bar--bar {
    color: #1DB954;
}

.progress-bar:hover > .bar--bar {
    color: #1ed760;
}

.progress-bar Bar {
    background: #535353;
    color: #1DB954;
}

ProgressBar > .bar--bar {
    color: #1DB954;
}

ProgressBar > .bar--complete {
    color: #1DB954;
}

ProgressBar > .bar--bar:hover {
    color: #1ed760;
}

/* ---- Volume Indicator ---- */
.volume {
    width: 12;
    height: 1;
}

.volume Bar {
    background: #535353;
    color: #1DB954;
}

.volume ProgressBar > .bar--bar {
    color: #1DB954;
}

.volume:hover ProgressBar > .bar--bar {
    color: #1ed760;
}

.volume-icon {
    width: 3;
    color: #B3B3B3;
}

.volume-icon:hover {
    color: #FFFFFF;
}

/* ---- Track List ---- */
.track-list {
    height: auto;
    width: 100%;
}

.track-item {
    layout: horizontal;
    height: 3;
    padding: 0 2;
    color: #B3B3B3;
    content-align-vertical: middle;
}

.track-item:hover {
    background: #282828;
    color: #FFFFFF;
}

.track-item:focus {
    background: #282828;
    color: #FFFFFF;
}

.track-item.--playing {
    color: #1DB954;
}

.track-item.--playing:hover {
    color: #1ed760;
}

.track-item.--even {
    background: #121212;
}

.track-item.--odd {
    background: #141414;
}

.track-item.--even:hover {
    background: #282828;
}

.track-item.--odd:hover {
    background: #282828;
}

.track-item .track-number {
    width: 4;
    color: #727272;
    content-align: right middle;
    padding-right: 1;
}

.track-item:hover .track-number {
    color: #FFFFFF;
}

.track-item .track-title-col {
    width: 2fr;
}

.track-item .track-title-col .title {
    color: #FFFFFF;
}

.track-item.--playing .track-title-col .title {
    color: #1DB954;
}

.track-item .track-title-col .artist {
    color: #727272;
}

.track-item:hover .track-title-col .artist {
    color: #B3B3B3;
}

.track-item .track-album-col {
    width: 1fr;
    color: #B3B3B3;
}

.track-item:hover .track-album-col {
    color: #FFFFFF;
}

.track-item .track-duration-col {
    width: 6;
    color: #727272;
    content-align: right middle;
}

.track-item .track-added-col {
    width: 12;
    color: #727272;
    content-align: right middle;
}

.track-list-header {
    layout: horizontal;
    height: 2;
    padding: 0 2;
    color: #727272;
    border-bottom: solid #282828;
    text-style: bold;

}

/* ---- Playlist Items / Cards ---- */
.playlist-item {
    height: 5;
    padding: 1 2;
    margin: 0 0 1 0;
    background: #181818;
    color: #FFFFFF;
}

.playlist-item:hover {
    background: #282828;
}

.playlist-item:focus {
    background: #333333;
    border-left: thick #1DB954;
}

.playlist-item .playlist-name {
    text-style: bold;
    color: #FFFFFF;
}

.playlist-item .playlist-desc {
    color: #727272;
}

.playlist-item .playlist-meta {
    color: #B3B3B3;
}

.playlist-grid {
    layout: grid;
    grid-size: 3;
    grid-gutter: 1;
    grid-rows: auto;
    padding: 1;
}

.playlist-card {
    height: auto;
    min-height: 6;
    padding: 1 2;
    background: #181818;
    color: #FFFFFF;
}

.playlist-card:hover {
    background: #282828;
}

.playlist-card:focus {
    background: #333333;
}

.playlist-card .card-title {
    text-style: bold;
    color: #FFFFFF;
}

.playlist-card .card-subtitle {
    color: #727272;
}

/* ---- Search Bar ---- */
#search-bar {
    height: 3;
    width: 100%;
    margin-bottom: 1;
}

#search-bar Input {
    background: #333333;
    color: #FFFFFF;
    border: tall #535353;
    padding: 0 2;
}

#search-bar Input:focus {
    border: tall #1DB954;
    background: #3E3E3E;
}

#search-bar Input.-placeholder {
    color: #727272;
}

Input {
    background: #333333;
    color: #FFFFFF;
    border: tall #535353;
}

Input:focus {
    border: tall #1DB954;
    background: #3E3E3E;
}

/* ---- DataTable ---- */
DataTable {
    background: #121212;
    color: #B3B3B3;
    height: 1fr;
}

DataTable > .datatable--header {
    background: #121212;
    color: #B3B3B3;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #282828;
    color: #1DB954;
    text-style: bold;
}

DataTable > .datatable--hover {
    background: #1a1a1a;
    color: #FFFFFF;
}

DataTable > .datatable--even-row {
    background: #121212;
}

DataTable > .datatable--odd-row {
    background: #141414;
}

DataTable > .datatable--header-hover {
    background: #1a1a1a;
    color: #FFFFFF;
}

/* ---- Device Selector ---- */
.device-list {
    height: auto;
    padding: 1;
}

.device-item {
    height: 3;
    padding: 0 2;
    color: #B3B3B3;
    content-align-vertical: middle;
}

.device-item:hover {
    background: #282828;
    color: #FFFFFF;
}

.device-item:focus {
    background: #282828;
    color: #FFFFFF;
}

.device-item.--active {
    color: #1DB954;
    text-style: bold;
    border-left: thick #1DB954;
    background: #1a1a1a;
}

.device-item .device-name {
    text-style: bold;
}

.device-item .device-type {
    color: #727272;
}

.device-item.--active .device-type {
    color: #1DB954;
}

/* ---- Buttons / Controls ---- */
Button {
    background: transparent;
    color: #B3B3B3;
    border: tall #535353;
    min-width: 10;
    height: 3;
}

Button:hover {
    background: #282828;
    color: #FFFFFF;
    border: tall #727272;
}

Button:focus {
    background: #333333;
    color: #FFFFFF;
    border: tall #1DB954;
}

Button.--primary {
    background: #1DB954;
    color: #FFFFFF;
    text-style: bold;
    border: tall #1DB954;
}

Button.--primary:hover {
    background: #1ed760;
    border: tall #1ed760;
}

Button.--active {
    color: #1DB954;
    border: tall #1DB954;
}

Button.--active:hover {
    color: #1ed760;
    border: tall #1ed760;
}

Button.--muted {
    color: #535353;
    border: tall #333333;
}

Button.--danger {
    color: #E22134;
    border: tall #E22134;
}

Button.--danger:hover {
    background: #E22134;
    color: #FFFFFF;
}

Button.--warning {
    color: #F5A623;
    border: tall #F5A623;
}

/* ---- Scrollbars ---- */
Scrollbar {
    background: #181818;
    color: #535353;
    width: 1;
}

ScrollBar > .scrollbar--bar {
    color: #535353;
}

ScrollBar > .scrollbar--bar:hover {
    color: #727272;
}

ScrollBar > .scrollbar--bar-active {
    color: #B3B3B3;
}

/* ---- Splash / Welcome Screen ---- */
/* ---- App Layout ---- */
#app-root {
    height: 100%;
    width: 100%;
}

#top-bar {
    dock: top;
    height: 3;
    background: #181818;
    border-bottom: solid #1DB954;
    padding: 1 2;
}

#top-logo {
    width: auto;
}

#top-device {
    width: 1fr;
    text-align: right;
    color: #B3B3B3;
}

#main-tabs {
    height: 1fr;
}

/* ---- Now Playing View ---- */
#now-playing-view {
    width: 100%;
    height: 100%;
    padding: 1 2;
}

#logo-art {
    color: #1DB954;
    text-align: center;
    width: 100%;
    height: auto;
}

#np-track-info {
    width: 100%;
    height: auto;
}

#np-progress-area {
    width: 100%;
    height: auto;
}

#np-controls-area {
    width: 100%;
    height: auto;
}

/* ---- Playlists Layout ---- */
#playlists-layout {
    width: 100%;
    height: 100%;
}

#playlists-sidebar {
    width: 30;
    background: #181818;
    border-right: solid #282828;
    padding: 1;
}

#playlists-detail {
    width: 1fr;
    padding: 1;
}

/* ---- Library Layout ---- */
#library-container {
    width: 100%;
    height: 100%;
    padding: 1;
}

/* ---- Search Layout ---- */
#search-container {
    width: 100%;
    height: 100%;
    padding: 1;
}

#search-results {
    height: 1fr;
}

/* ---- Device Modal ---- */
#device-modal {
    width: 50;
    height: auto;
    max-height: 70%;
    background: #282828;
    border: tall #535353;
    padding: 2;
    align: center middle;
}

#device-title {
    padding-bottom: 1;
}

#device-list {
    height: auto;
    max-height: 20;
    margin-bottom: 1;
}

#device-cancel {
    width: 100%;
}

.splash {
    width: 100%;
    height: 100%;
    content-align: center middle;
    background: #121212;
}

.splash .logo {
    text-align: center;
    color: #1DB954;
    text-style: bold;
    width: auto;
    height: auto;
    padding: 1;
}

.splash .logo-glow {
    text-align: center;
    color: #1ed760;
    text-style: bold;
    width: auto;
    height: auto;
}

.splash .tagline {
    text-align: center;
    color: #727272;
    padding: 1 0 0 0;
    width: auto;
    height: auto;
}

.splash .version {
    text-align: center;
    color: #535353;
    padding: 0;
    width: auto;
    height: auto;
}

.splash .instructions {
    text-align: center;
    color: #B3B3B3;
    padding: 2 0 0 0;
    width: auto;
    height: auto;
}

/* ---- Tabs ---- */
Tabs {
    background: #121212;
    height: 3;
}

Tab {
    background: #121212;
    color: #B3B3B3;
    padding: 0 3;
}

Tab:hover {
    color: #FFFFFF;
    background: #1a1a1a;
}

Tab.-active {
    color: #FFFFFF;
    text-style: bold;
}

Underline > .underline--bar {
    color: #1DB954;
}

/* ---- Notifications / Toasts ---- */
Toast {
    background: #282828;
    color: #FFFFFF;
    border: tall #535353;
}

Toast.-information {
    border: tall #1DB954;
}

Toast.-warning {
    border: tall #F5A623;
}

Toast.-error {
    border: tall #E22134;
}

/* ---- Labels / Text ---- */
.text-primary {
    color: #FFFFFF;
}

.text-secondary {
    color: #B3B3B3;
}

.text-muted {
    color: #727272;
}

.text-accent {
    color: #1DB954;
}

.text-error {
    color: #E22134;
}

.text-warning {
    color: #F5A623;
}

.text-bold {
    text-style: bold;
}

/* ---- Modals / Overlays ---- */
.modal-overlay {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

.modal-container {
    width: 60;
    height: auto;
    max-height: 80%;
    background: #282828;
    border: tall #535353;
    padding: 2;
}

.modal-container .modal-title {
    text-style: bold;
    color: #FFFFFF;
    padding-bottom: 1;
}

.modal-container .modal-body {
    color: #B3B3B3;
    padding-bottom: 1;
}

/* ---- Context Menu ---- */
.context-menu {
    background: #282828;
    border: tall #535353;
    padding: 1 0;
    width: auto;
    min-width: 20;
}

.context-menu-item {
    padding: 0 2;
    height: 2;
    color: #B3B3B3;
    content-align-vertical: middle;
}

.context-menu-item:hover {
    background: #333333;
    color: #FFFFFF;
}

.context-menu-separator {
    height: 1;
    background: #535353;
    margin: 0 1;
}

/* ---- Footer / Status Bar ---- */
Footer {
    background: #181818;
    color: #727272;
}

Footer > .footer--highlight {
    background: #1DB954;
    color: #FFFFFF;
}

Footer > .footer--key {
    background: #282828;
    color: #B3B3B3;
}

Footer > .footer--highlight-key {
    background: #1DB954;
    color: #FFFFFF;
    text-style: bold;
}

/* ---- Loading / Spinner ---- */
.loading-container {
    width: 100%;
    height: 100%;
    content-align: center middle;
    color: #1DB954;
}

LoadingIndicator {
    color: #1DB954;
}

/* ---- Queue View ---- */
.queue-item {
    height: 3;
    padding: 0 2;
    color: #B3B3B3;
    content-align-vertical: middle;
}

.queue-item:hover {
    background: #282828;
    color: #FFFFFF;
}

.queue-item.--current {
    color: #1DB954;
    text-style: bold;
}

.queue-item .queue-position {
    width: 4;
    color: #727272;
    content-align: right middle;
}

/* ---- Empty State ---- */
.empty-state {
    width: 100%;
    height: 100%;
    content-align: center middle;
    color: #727272;
}

.empty-state .empty-icon {
    color: #535353;
    text-align: center;
}

.empty-state .empty-message {
    color: #727272;
    text-align: center;
    padding: 1 0;
}

/* ---- Album / Artist Header ---- */
.detail-header {
    height: auto;
    padding: 1 2;
    background: #181818;
    margin-bottom: 1;
}

.detail-header .detail-title {
    text-style: bold;
    color: #FFFFFF;
}

.detail-header .detail-subtitle {
    color: #B3B3B3;
}

.detail-header .detail-meta {
    color: #727272;
}

/* ---- Selection / Checkbox ---- */
Checkbox {
    background: transparent;
    color: #B3B3B3;
}

Checkbox:hover {
    color: #FFFFFF;
}

Checkbox.-on > .toggle--button {
    color: #1DB954;
}

/* ---- Tooltip ---- */
.tooltip {
    background: #282828;
    color: #FFFFFF;
    border: tall #535353;
    padding: 0 1;
}

/* ---- Horizontal Rule ---- */
Rule {
    color: #282828;
}

Rule.-horizontal {
    margin: 1 0;
}

/* ---- ListItem generic ---- */
ListItem {
    background: transparent;
    color: #B3B3B3;
}

ListItem:hover {
    background: #282828;
    color: #FFFFFF;
}

ListItem.-highlight {
    background: #282828;
    color: #FFFFFF;
}

ListView {
    background: transparent;
}

ListView > ListItem.--highlight {
    background: #282828;
}

/* ---- Tree widget ---- */
Tree {
    background: transparent;
    color: #B3B3B3;
}

Tree > .tree--cursor {
    background: #282828;
    color: #1DB954;
    text-style: bold;
}

Tree > .tree--highlight {
    background: #1a1a1a;
}

Tree > .tree--guides {
    color: #333333;
}

/* ---- OptionList ---- */
OptionList {
    background: #181818;
    color: #B3B3B3;
    border: tall #333333;
}

OptionList > .option-list--option-highlighted {
    background: #282828;
    color: #FFFFFF;
}

OptionList > .option-list--option-hover {
    background: #1a1a1a;
}

/* ---- Select / Dropdown ---- */
Select {
    background: #333333;
    color: #FFFFFF;
    border: tall #535353;
}

Select:focus {
    border: tall #1DB954;
}

SelectOverlay {
    background: #282828;
    color: #B3B3B3;
    border: tall #535353;
}

SelectOverlay > .option-list--option-highlighted {
    background: #333333;
    color: #FFFFFF;
}
"""
