import numpy as np
import pytest
import scanpy as sc
from scipy.sparse import csr_matrix

import triku as tk


@pytest.fixture
def getpbmc3k():
    adata = sc.datasets.pbmc3k()
    sc.pp.filter_genes(adata, min_cells=10)
    sc.pp.filter_cells(adata, min_genes=10)
    sc.pp.neighbors(adata)

    return adata


@pytest.mark.exception_check
def test_triku_check_count_mat_20000_vars():
    adata = sc.datasets.blobs(
        n_variables=22000, n_centers=3, cluster_std=1, n_observations=500
    )
    adata.X = np.abs(adata.X).astype(int)
    print(adata.X)

    sc.pp.filter_cells(adata, min_genes=10)
    sc.pp.filter_genes(adata, min_cells=1)

    sc.pp.pca(adata)
    sc.pp.neighbors(adata)

    assert adata.X.shape[1] > 20000

    tk.tl.triku(adata)


@pytest.mark.exception_check
def test_triku_check_nonaccepted_type():
    adata = sc.datasets.blobs(
        n_variables=2000, n_centers=3, cluster_std=1, n_observations=500
    )
    adata.X = np.abs(adata.X).astype(int)
    adata.var_names = [0] + list(np.arange(len(adata.var_names) - 1))

    try:
        tk.tl.triku(adata.X)
    except BaseException:
        pass
    else:
        raise BaseException


@pytest.mark.exception_check
def test_triku_dense_sparse_matrices(getpbmc3k):
    adata_dense = getpbmc3k
    adata_sparse = getpbmc3k.copy()

    adata_dense.X = adata_dense.X.toarray()
    adata_sparse.X = csr_matrix(adata_sparse.X)

    tk.tl.triku(adata_sparse)
    tk.tl.triku(adata_dense)

    for key in ["knn", "n_features", "s", "n_windows", "min_knn", "dist_conn"]:
        assert (
            adata_sparse.uns["triku_params"]["None"][key]
            == adata_dense.uns["triku_params"]["None"][key]
        )

    assert (
        adata_sparse.uns["triku_params"]["None"]["knn_array"]
        != adata_dense.uns["triku_params"]["None"]["knn_array"]
    ).nnz == 0

    assert np.all(
        adata_dense.var["triku_distance"] == adata_sparse.var["triku_distance"]
    )


@pytest.mark.exception_check
def test_triku_dense_sparse_matrices_raw(getpbmc3k):
    adata_dense = getpbmc3k
    adata_sparse = getpbmc3k.copy()

    adata_dense.X = adata_dense.X.toarray()
    adata_sparse.X = csr_matrix(adata_sparse.X)

    adata_dense.raw = adata_dense
    adata_sparse.raw = adata_sparse

    tk.tl.triku(adata_sparse, use_raw=True)
    tk.tl.triku(adata_dense, use_raw=True)

    for key in ["knn", "n_features", "s", "n_windows", "min_knn", "dist_conn"]:
        assert (
            adata_sparse.uns["triku_params"]["None"][key]
            == adata_dense.uns["triku_params"]["None"][key]
        )

    assert (
        adata_sparse.uns["triku_params"]["None"]["knn_array"]
        != adata_dense.uns["triku_params"]["None"]["knn_array"]
    ).nnz == 0

    assert np.all(
        adata_dense.var["triku_distance"] == adata_sparse.var["triku_distance"]
    )


@pytest.mark.exception_check
def test_check_count_mat_negative(getpbmc3k):
    adata = getpbmc3k

    adata.X[0, 0] = -1

    try:
        tk.tl.triku(adata)
        error = 1
    except BaseException:
        error = 0

    if error == 1:
        raise


@pytest.mark.exception_check
def test_check_zero_counts():
    adata = sc.datasets.pbmc3k()
    sc.pp.neighbors(adata)

    try:
        tk.tl.triku(
            adata
        )  # There should be zeros and raise an error -> therefore it should yield error = 0
        error = 1
    except BaseException:
        error = 0

    if error == 1:
        raise

    adata_nonzero = sc.datasets.pbmc3k()
    sc.pp.filter_genes(adata_nonzero, min_counts=1)
    sc.pp.neighbors(adata_nonzero)

    tk.tl.triku(adata_nonzero)
