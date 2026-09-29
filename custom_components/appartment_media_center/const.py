"""Constants for the bundled integration."""
DOMAIN = "appartment_media_center"
VERSION = "1.1.0"
CARD_URL = f"/appartment_media_center/showreel-mode-card.js?v={VERSION}"
MODES = {
    "Automatico": "auto",
    "Showreel video": "showreel",
    "Showreel foto": "photos",
    "Schermo nero": "black",
    "Riunione": "meeting",
}

# key: (name, action, arguments, icon)
BUTTONS = {
    "release_screen": ("Libera schermo", "release_screen", {}, "mdi:cast-off"),
    "refresh_showreel": ("Aggiorna video", "refresh_showreel", {}, "mdi:movie-refresh"),
    "refresh_photos": ("Aggiorna foto", "refresh_photos", {}, "mdi:image-refresh"),
    "sync_content": ("Sincronizza contenuti", "sync_content", {}, "mdi:cloud-download"),
    "previous_page": ("Pagina precedente", "presentation_control", {"operation": "previous"}, "mdi:chevron-left"),
    "next_page": ("Pagina successiva", "presentation_control", {"operation": "next"}, "mdi:chevron-right"),
    "close_presentation": ("Chiudi presentazione", "close_presentation", {}, "mdi:presentation"),
}
CONTROL_TYPES = {"volume": "number", "muted": "switch", "meeting_title": "text",
                 **{key: "button" for key in BUTTONS}}
