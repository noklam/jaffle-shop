from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, ClassVar

import ibis.expr.types as ir
from kedro.io import AbstractDataset, DatasetError

if TYPE_CHECKING:
    from ibis import BaseBackend


class TableDataset(AbstractDataset[ir.Table, ir.Table]):
    _connections: ClassVar[dict[tuple[tuple[str, str]], BaseBackend]] = {}

    def __init__(
        self,
        *,
        filepath: str | None = None,
        file_format: str | None = None,
        table_name: str | None = None,
        connection: dict[str, Any] | None = None,
        load_args: dict[str, Any] | None = None,
        save_args: dict[str, Any] | None = None,
    ) -> None:
        if filepath is None and table_name is None:
            raise DatasetError(
                "Must provide at least one of `filepath` or `table_name`."
            )

        self._filepath = filepath
        self._file_format = file_format
        self._table_name = table_name
        self._connection_config = connection
        self._load_args = {} if load_args is None else deepcopy(load_args)
        self._save_args = {} if save_args is None else deepcopy(save_args)

    @property
    def connection(self) -> BaseBackend:
        cls = type(self)
        key = tuple(sorted(self._connection_config.items()))
        if key not in cls._connections:
            import ibis

            config = deepcopy(self._connection_config)
            backend = getattr(ibis, config.pop("backend"))
            cls._connections[key] = backend.connect(**config)

        return cls._connections[key]

    def _load(self) -> ir.Table:
        if self._filepath is not None:
            if self._file_format is None:
                raise NotImplementedError

            reader = getattr(self.connection, f"read_{self._file_format}")
            return reader(self._filepath, self._table_name, **self._load_args)
        else:
            return self.connection.table(self._table_name)

    def _save(self, data: ir.Table) -> None:
        raise NotImplementedError

    def _describe(self) -> dict[str, Any]:
        return {
            "filepath": self._filepath,
            "file_format": self._file_format,
            "table_name": self._table_name,
            "connection_config": self._connection_config,
            "load_args": self._load_args,
            "save_args": self._save_args,
        }