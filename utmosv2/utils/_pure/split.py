from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

import numpy as np

from utmosv2._import import _LazyImport
from utmosv2._settings._config import Config

if TYPE_CHECKING:
    import pandas as pd
    from sklearn.model_selection import (
        GroupKFold,
        KFold,
        StratifiedGroupKFold,
        StratifiedKFold,
    )
else:
    _model_selection = _LazyImport("sklearn.model_selection")
    GroupKFold = _model_selection.GroupKFold
    KFold = _model_selection.KFold
    StratifiedGroupKFold = _model_selection.StratifiedGroupKFold
    StratifiedKFold = _model_selection.StratifiedKFold


def split_data(
    cfg: Config, data: "pd.DataFrame"
) -> Generator[tuple[np.ndarray, np.ndarray], None, None]:
    """
    Split the data into training and validation sets based on the specified splitting method in the configuration.

    Args:
        cfg (SimpleNamespace | ModuleType): Configuration object containing the splitting settings. It includes:
            - split.type: Type of split to use ('simple', 'stratified', 'group', 'stratified_group', etc.).
            - num_folds: Number of folds for K-Fold cross-validation.
            - split.seed: Random seed for shuffling.
            - split.target: Target column used for stratification in 'stratified' and 'stratified_group'.
            - split.group: Group column used for grouping in 'group' and 'stratified_group'.
            - split.kind: Kind of data for splitting in the 'sgkf_kind' case.
        data (pd.DataFrame): The dataset to be split.

    Yields:
        tuple[np.ndarray, np.ndarray]: Indices of training and validation sets for each fold.

    Raises:
        NotImplementedError: If the split type specified in the configuration is not implemented.
    """
    if cfg.print_config:
        print(f"Using split: {cfg.split.type}")
    if cfg.split.type == "simple":
        kf = KFold(n_splits=cfg.num_folds, shuffle=True, random_state=cfg.split.seed)
        for train_idx, valid_idx in kf.split(data):
            yield train_idx, valid_idx
    elif cfg.split.type == "stratified":
        kf = StratifiedKFold(
            n_splits=cfg.num_folds, shuffle=True, random_state=cfg.split.seed
        )
        for train_idx, valid_idx in kf.split(data, data[cfg.split.target].astype(int)):
            yield train_idx, valid_idx
    elif cfg.split.type == "group":
        kf = GroupKFold(n_splits=cfg.num_folds)
        for train_idx, valid_idx in kf.split(data, groups=data[cfg.split.group]):
            yield train_idx, valid_idx
    elif cfg.split.type == "stratified_group":
        kf = StratifiedGroupKFold(
            n_splits=cfg.num_folds, shuffle=True, random_state=cfg.split.seed
        )
        for train_idx, valid_idx in kf.split(
            data, data[cfg.split.target].astype(int), groups=data[cfg.split.group]
        ):
            yield train_idx, valid_idx
    elif cfg.split.type == "sgkf_kind":
        kind = data[cfg.split.kind].unique()
        kf = [
            StratifiedGroupKFold(
                n_splits=cfg.num_folds, shuffle=True, random_state=cfg.split.seed
            )
            for _ in range(len(kind))
        ]
        kf = [
            kf_i.split(
                data[data[cfg.split.kind] == ds],
                data[data[cfg.split.kind] == ds][cfg.split.target].astype(int),
                groups=data[data[cfg.split.kind] == ds][cfg.split.group],
            )
            for kf_i, ds in zip(kf, kind)
        ]
        for ds_idx in zip(*kf):
            train_idx = np.concatenate([d[0] for d in ds_idx])
            valid_idx = np.concatenate([d[1] for d in ds_idx])
            yield train_idx, valid_idx
    else:
        raise NotImplementedError
