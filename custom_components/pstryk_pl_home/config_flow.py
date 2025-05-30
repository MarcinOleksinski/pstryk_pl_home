"""Config- oraz Options-flow integracji Pstryk.pl Home."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_API_TOKEN,
    CONF_ENTITY_PREFIX,
    DEFAULT_ENTITY_PREFIX,
)

_VALID_PREFIX = re.compile(r"^[a-z0-9_]+$")  # bez spacji, wielkich liter


class PstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Dodawanie integracji w UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Pierwszy (i jedyny) krok: token + opcjonalny prefiks."""
        if user_input is not None:
            prefix = user_input.get(CONF_ENTITY_PREFIX, "").strip().lower()
            errors: dict[str, str] = {}

            if prefix and not _VALID_PREFIX.fullmatch(prefix):
                errors[CONF_ENTITY_PREFIX] = "invalid_prefix"
            if not prefix:
                prefix = DEFAULT_ENTITY_PREFIX

            if errors:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._schema(user_input),
                    errors=errors,
                )

            user_input[CONF_ENTITY_PREFIX] = prefix
            return self.async_create_entry(
                title=f"Pstryk.pl ({prefix})", data=user_input
            )

        return self.async_show_form(step_id="user", data_schema=self._schema())

    # ---------- helpers ---------- #
    @staticmethod
    def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
        defaults = defaults or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_TOKEN, default=defaults.get(CONF_API_TOKEN, "")
                ): str,
                vol.Optional(
                    CONF_ENTITY_PREFIX,
                    default=defaults.get(CONF_ENTITY_PREFIX, DEFAULT_ENTITY_PREFIX),
                ): str,
            }
        )

    # ---------- options flow ---------- #
    @callback
    def async_get_options_flow(self, config_entry):  # ← poprawiona sygnatura
        return PstrykOptionsFlow(config_entry)


class PstrykOptionsFlow(config_entries.OptionsFlow):
    """Edycja tokenu / prefiksu po instalacji."""

    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            prefix = user_input[CONF_ENTITY_PREFIX].strip().lower()
            errors = {}

            if not _VALID_PREFIX.fullmatch(prefix):
                errors[CONF_ENTITY_PREFIX] = "invalid_prefix"

            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(user_input),
                    errors=errors,
                )

            await self._entry.async_set_options(user_input)
            return self.async_create_entry(data=user_input)

        return self.async_show_form(step_id="init", data_schema=self._schema())

    def _schema(self, defaults: dict[str, Any] | None = None) -> vol.Schema:
        defaults = defaults or self._entry.options
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_TOKEN,
                    default=defaults.get(CONF_API_TOKEN, self._entry.data[CONF_API_TOKEN]),
                ): str,
                vol.Required(
                    CONF_ENTITY_PREFIX,
                    default=defaults.get(
                        CONF_ENTITY_PREFIX, self._entry.data[CONF_ENTITY_PREFIX]
                    ),
                ): str,
            }
        )