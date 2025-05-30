"""UI config flow dla Pstryk.pl Home."""
from __future__ import annotations

import voluptuous as vol
import re
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_API_TOKEN,
    CONF_ENTITY_PREFIX,
    DEFAULT_ENTITY_PREFIX,
)

_VALID_PREFIX = re.compile(r"^[a-z0-9_]+$")  # bez spacji / wielkich liter

class PstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Tworzenie konfiguracji."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Pierwszy (i jedyny) krok – token + prefiks."""
        if user_input is not None:
            prefix = user_input.get(CONF_ENTITY_PREFIX, "").strip().lower()
            if prefix and not _VALID_PREFIX.fullmatch(prefix):
                return self.async_show_form(
                    step_id="user",
                    errors={"entity_prefix": "invalid_prefix"},
                    data_schema=self._schema(user_input),
                )

            # wpis pusty → domyślny prefiks
            if not prefix:
                prefix = DEFAULT_ENTITY_PREFIX
            user_input[CONF_ENTITY_PREFIX] = prefix

            return self.async_create_entry(
                title=f"Pstryk.pl ({prefix})",
                data=user_input,
            )

        return self.async_show_form(step_id="user", data_schema=self._schema())

    def _schema(self, defaults=None):
        """Schema helper."""
        defaults = defaults or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_TOKEN,
                    default=defaults.get(CONF_API_TOKEN, ""),
                ): str,
                vol.Optional(
                    CONF_ENTITY_PREFIX,
                    description={"suggested_value": DEFAULT_ENTITY_PREFIX},
                    default=defaults.get(CONF_ENTITY_PREFIX, DEFAULT_ENTITY_PREFIX),
                ): str,
            }
        )

    @callback
    def async_get_options_flow(self, entry):
        return PstrykOptionsFlow(entry)


class PstrykOptionsFlow(config_entries.OptionsFlow):
    """Edycja tokenu / prefiksu po instalacji."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            prefix = user_input[CONF_ENTITY_PREFIX].strip().lower()
            errors = {}
            if not _VALID_PREFIX.fullmatch(prefix):
                errors["entity_prefix"] = "invalid_prefix"
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(user_input),
                    errors=errors,
                )

            await self.entry.async_set_options(user_input)
            return self.async_create_entry(data=user_input)

        return self.async_show_form(step_id="init", data_schema=self._schema())

    def _schema(self, defaults=None):
        defaults = defaults or self.entry.options
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_TOKEN,
                    default=defaults.get(CONF_API_TOKEN, self.entry.data[CONF_API_TOKEN]),
                ): str,
                vol.Required(
                    CONF_ENTITY_PREFIX,
                    default=defaults.get(
                        CONF_ENTITY_PREFIX, self.entry.data[CONF_ENTITY_PREFIX]
                    ),
                ): str,
            }
        )