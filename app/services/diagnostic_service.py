"""
DiagnosticService
=================

Core business-logic layer for the Diagnostic Engine.

Responsibilities
----------------
* Load the OBD-II DTC dataset from CSV **once** at startup and keep the
  ``pandas.DataFrame`` in memory for the lifetime of the process.
* Expose ``get_dtc(code)`` for exact-match lookups.
* Expose ``search(keyword)`` for free-text search across description,
  subsystem, and category columns.
* Expose ``get_statistics()`` for dataset-level aggregations.

This class has **no FastAPI dependency** and can be tested in isolation.
"""

from __future__ import annotations

import pandas as pd

from app.config import settings
from app.models.dtc import (
    DTCResponse,
    DTCSearchResult,
    SearchResponse,
    StatisticsResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DiagnosticService:
    """
    Knowledge-based service that wraps an in-memory OBD-II DTC dataset.

    Parameters
    ----------
    dataset_path:
        Path to the CSV file.  Defaults to ``settings.DATASET_PATH``.

    Usage
    -----
    Instantiate once (via FastAPI ``Depends`` / lifespan) and share the
    instance across requests.
    """

    def __init__(self, dataset_path: str | None = None) -> None:
        self._dataset_path: str = dataset_path or settings.DATASET_PATH
        self._df: pd.DataFrame = pd.DataFrame()

    # ------------------------------------------------------------------
    # Dataset management
    # ------------------------------------------------------------------

    def load_dataset(self) -> None:
        """
        Read the CSV from disk into ``self._df``.

        * Normalises the ``dtc_code`` column to uppercase and strips
          surrounding whitespace so lookups are case-insensitive.
        * Sets ``dtc_code`` as the DataFrame index for O(1) lookups.
        * Logs a warning if the file is empty or missing columns.

        Raises
        ------
        FileNotFoundError
            If the CSV file does not exist at the configured path.
        ValueError
            If required columns are absent from the CSV.
        """
        logger.info("Loading dataset from '%s' …", self._dataset_path)

        required_columns = {
            "dtc_code",
            "description",
            "subsystem",
            "category",
            "severity",
            "severity_score",
            "safe_to_drive",
            "immediate_repair",
            "explanation",
            "driver_action",
        }

        df = pd.read_csv(self._dataset_path, dtype=str)

        missing = required_columns - set(df.columns)
        if missing:
            raise ValueError(
                f"Dataset is missing required columns: {missing}"
            )

        # Normalise the key column
        df["dtc_code"] = df["dtc_code"].str.strip().str.upper()

        # Convert severity_score to int (fill bad values with 0)
        df["severity_score"] = pd.to_numeric(
            df["severity_score"], errors="coerce"
        ).fillna(0).astype(int)

        # Use dtc_code as index for fast exact lookups
        df = df.set_index("dtc_code")

        self._df = df
        logger.info(
            "Dataset loaded successfully — %d DTC records available.",
            len(self._df),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_dtc(self, code: str) -> DTCResponse | None:
        """
        Return the full diagnostic record for a single DTC code.

        Parameters
        ----------
        code:
            The DTC code to look up (e.g. ``"P0301"``).
            Matching is **case-insensitive**.

        Returns
        -------
        DTCResponse
            The matched record.
        None
            If the code does not exist in the dataset.
        """
        normalised = code.strip().upper()
        logger.debug("Looking up DTC code: %s", normalised)

        if normalised not in self._df.index:
            logger.info("DTC code not found: %s", normalised)
            return None

        row = self._df.loc[normalised]

        # ``loc`` returns a Series for a single hit; a DataFrame for
        # duplicate index entries.  We always take the first match.
        if isinstance(row, pd.DataFrame):
            logger.warning(
                "Duplicate index entries for code '%s'; returning first.",
                normalised,
            )
            row = row.iloc[0]

        return DTCResponse(
            dtc=normalised,
            description=str(row["description"]),
            subsystem=str(row["subsystem"]),
            category=str(row["category"]),
            severity=str(row["severity"]),
            severity_score=int(row["severity_score"]),
            safe_to_drive=str(row["safe_to_drive"]),
            immediate_repair=str(row["immediate_repair"]),
            explanation=str(row["explanation"]),
            driver_action=str(row["driver_action"]),
        )

    def search(self, keyword: str) -> SearchResponse:
        """
        Full-text search across ``description``, ``subsystem``, and
        ``category`` columns.

        The search is **case-insensitive** and uses substring matching.

        Parameters
        ----------
        keyword:
            The term to search for.

        Returns
        -------
        SearchResponse
            A wrapper object containing the keyword, total match count,
            and a list of matching :class:`DTCSearchResult` records.
        """
        logger.debug("Searching for keyword: '%s'", keyword)

        if not keyword or not keyword.strip():
            logger.info("Empty keyword — returning empty search results.")
            return SearchResponse(keyword=keyword, total=0, results=[])

        kw = keyword.strip().lower()

        mask = (
            self._df["description"].str.lower().str.contains(kw, na=False)
            | self._df["subsystem"].str.lower().str.contains(kw, na=False)
            | self._df["category"].str.lower().str.contains(kw, na=False)
        )

        matches = self._df[mask]
        logger.info(
            "Search for '%s' returned %d result(s).", keyword, len(matches)
        )

        results = [
            DTCSearchResult(
                dtc=str(idx),
                description=str(row["description"]),
                subsystem=str(row["subsystem"]),
                category=str(row["category"]),
                severity=str(row["severity"]),
                severity_score=int(row["severity_score"]),
                safe_to_drive=str(row["safe_to_drive"]),
                immediate_repair=str(row["immediate_repair"]),
            )
            for idx, row in matches.iterrows()
        ]

        return SearchResponse(keyword=keyword, total=len(results), results=results)

    def get_statistics(self) -> StatisticsResponse:
        """
        Compute and return dataset-level statistics.

        Aggregations are computed on the fly from the in-memory
        DataFrame each time this method is called.  For a dataset of
        this size the overhead is negligible; if the dataset grows
        significantly, caching the result at load time would be trivial.

        Returns
        -------
        StatisticsResponse
            Total DTC count plus distribution dicts for severity,
            category, and subsystem.
        """
        logger.debug("Computing dataset statistics.")

        severity_dist: dict[str, int] = (
            self._df["severity"]
            .value_counts()
            .to_dict()
        )
        category_dist: dict[str, int] = (
            self._df["category"]
            .value_counts()
            .to_dict()
        )
        subsystem_dist: dict[str, int] = (
            self._df["subsystem"]
            .value_counts()
            .to_dict()
        )

        return StatisticsResponse(
            total_dtcs=len(self._df),
            severity_distribution=severity_dist,
            category_distribution=category_dist,
            subsystem_distribution=subsystem_dist,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` if the dataset has been loaded."""
        return not self._df.empty
