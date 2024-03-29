# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Plugin managing the icon themes for the application.

"""
import logging
from traceback import format_exc
from typing import Any, Mapping

from atom.api import List, Str, Typed
from enaml.icon import Icon as EnamlIcon

from gild.utils.plugin_tools import (
    ExtensionsCollector,
    HasPreferencesPlugin,
    make_extension_validator,
)

from .icon_theme import IconTheme, IconThemeExtension

ICON_THEME_POINT = "gild.icons.icon_theme"

ICON_THEME_EXTENSION_POINT = "gild.icons.icon_theme_extension"


class IconManagerPlugin(HasPreferencesPlugin):
    """Plugin managing icon theme and access to icon for the application."""

    #: Id of the currently selected icon theme
    current_theme = Str("gild.FontAwesome").tag(pref=True)

    #: Id of the icon theme to use as fallback if a theme fail to provide an
    #: icon.
    fallback_theme = Str("gild.FontAwesome").tag(pref=True)

    #: Registered icon themes ids
    icon_themes = List()

    def start(self) -> None:
        """Start the plugin lifecycle and collect themes and extensions."""
        super(IconManagerPlugin, self).start()

        checker = make_extension_validator(IconTheme, (), ())
        self._icon_themes = ExtensionsCollector(
            workbench=self.workbench,
            point=ICON_THEME_POINT,
            ext_class=IconTheme,
            validate_ext=checker,
        )
        self._icon_themes.start()
        self._list_icon_themes({})

        if self.current_theme not in self.icon_themes:
            self.current_theme = self.icon_themes[0]

        if self.fallback_theme not in self.icon_themes:
            self.fallback_theme = "gild.FontAwesome"

        checker = make_extension_validator(IconThemeExtension, (), ("theme",))
        self._icon_theme_extensions = ExtensionsCollector(
            workbench=self.workbench,
            point=ICON_THEME_EXTENSION_POINT,
            ext_class=IconThemeExtension,
            validate_ext=checker,
        )
        self._icon_theme_extensions.start()
        self._add_extensions_to_selected_theme({})

        self._bind_observers()

    def stop(self) -> None:
        """Stop the plugin and clean up."""
        self._unbind_observers()
        self._icon_theme_extensions.stop()
        self._icon_themes.stop()

    def get_icon(self, icon_id: str) -> EnamlIcon:
        """Get an icon from the selected theme.

        Fallback to fallback_theme if no matching icon is found in the selected
        theme.

        """
        icon_theme = self._icon_themes.contributions[self.current_theme]
        icon = None
        msg = ""
        try:
            icon = icon_theme.get_icon(self, icon_id)
        except Exception:
            msg = "Icon theme %s failed to provide icon %s and raised:\n%s"
            msg = msg % (self.current_theme, icon_id, format_exc())
        else:
            if icon is None:
                msg = "Icon theme %s failed to provide icon %s without errors."
                msg = msg % (self.current_theme, icon_id)

        if msg:
            fallback = self._icon_themes.contributions[self.fallback_theme]
            try:
                icon = fallback.get_icon(self, icon_id)
            except Exception:
                msg += "Fallback theme %s failed to provide icon %s and " "raised:\n%s"
                msg = msg % (self.fallback_theme, icon_id, format_exc())
            else:
                if icon is None:
                    msg += (
                        "Fallback theme %s failed to provide icon %s " "without errors."
                    )
                    msg = msg % (self.fallback_theme, icon_id)

            logger = logging.getLogger(__name__)
            logger.warning(msg)

        return icon

    # --- Private API ---------------------------------------------------------

    #: Collector for the declared icon themes.
    _icon_themes = Typed(ExtensionsCollector)

    #: Collector for the declared icon theme extensions.
    _icon_theme_extensions = Typed(ExtensionsCollector)

    #: Currently selected theme.
    _current_theme = Typed(IconTheme)

    def _add_extensions_to_selected_theme(self, change: Mapping[str, Any]) -> None:
        """Add contributed theme extension to the selected theme."""
        selected = self._current_theme

        # Assign all contributed icons from all extensions.
        if not change:
            for k, v in self._icon_theme_extensions.contributions.items():
                if v.theme == selected.id:
                    selected.insert_children(None, v.icons())

        # Only update icons provided by new extensions.
        else:
            added = set(change["value"]) - set(change.get("oldvalue", {}))
            removed = set(change.get("oldvalue", {})) - set(change["value"])
            ext = dict(change["value"])
            ext.update(change.get("oldvalue", {}))
            for k in added:
                v = ext[k]
                if v.theme == selected.id:
                    selected.insert_children(None, v.icons())
            for k in removed:
                v = ext[k]
                if v.theme == selected.id:
                    v.insert_children(None, v.icons())

        del selected._icons

    def _post_setattr_current_theme(self, old: str, new: str) -> None:
        """Add the extension icons to the theme."""
        del self._current_theme
        if self._icon_theme_extensions:
            self._add_extensions_to_selected_theme({})

    def _list_icon_themes(self, change: Mapping[str, Any]) -> None:
        """List the declared icon themes."""
        self.icon_themes = sorted(self._icon_themes.contributions)

    def _bind_observers(self) -> None:
        """Setup the observers on the contributions."""
        self._icon_themes.observe("contributions", self._list_icon_themes)
        self._icon_theme_extensions.observe(
            "contributions", self._add_extensions_to_selected_theme
        )

    def _unbind_observers(self) -> None:
        """Remove the observers on the contributions."""
        self._icon_themes.unobserve("contributions", self._list_icon_themes)
        self._icon_theme_extensions.unobserve(
            "contributions", self._add_extensions_to_selected_theme
        )

    def _default__current_theme(self) -> IconTheme:
        """Get the current theme object based on the current_theme member."""
        return self._icon_themes.contributions[self.current_theme]
