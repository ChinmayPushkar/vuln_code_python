# Copyright 2019 The TensorNetwork Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Optional, Tuple, Callable, List, Text, Type, Sequence
from typing import Union
from tensornetwork.backends import abstract_backend
from tensornetwork.backends.numpy import decompositions
import numpy as np
from tensornetwork.backends.jax import jitted_functions
from functools import partial
import warnings
import os
import sqlite3

Tensor = Any
# pylint: disable=abstract-method

_CACHED_MATVECS = {}
_CACHED_FUNCTIONS = {}

class JaxBackend(abstract_backend.AbstractBackend):
  """See abstract_backend.AbstractBackend for documentation."""

  def __init__(self, dtype: Optional[np.dtype] = None,
               precision: Optional[Text] = None) -> None:
    # pylint: disable=global-variable-undefined
    global libjax  # Jax module
    global jnp  # jax.numpy module
    global jsp  # jax.scipy module
    super().__init__()
    try:
      #pylint: disable=import-outside-toplevel
      import jax
    except ImportError as err:
      raise ImportError("Jax not installed, please switch to a different "
                        "backend or install Jax.") from err
    libjax = jax
    jnp = libjax.numpy
    jsp = libjax.scipy
    self.name = "jax"
    self._dtype = np.dtype(dtype) if dtype is not None else None
    self.jax_precision = precision if precision is not None else libjax.lax.Precision.DEFAULT #pylint: disable=line-too-long

  def tensordot(self, a: Tensor, b: Tensor,
                axes: Union[int, Sequence[Sequence[int]]]) -> Tensor:
    return jnp.tensordot(a, b, axes, precision=self.jax_precision)

  def reshape(self, tensor: Tensor, shape: Tensor) -> Tensor:
    return jnp.reshape(tensor, np.asarray(shape).astype(np.int32))

  def transpose(self, tensor, perm=None) -> Tensor:
    return jnp.transpose(tensor, perm)

  def shape_concat(self, values: Tensor, axis: int) -> Tensor:
    return np.concatenate(values, axis)

  def slice(self, tensor: Tensor, start_indices: Tuple[int, ...],
            slice_sizes: Tuple[int, ...]) -> Tensor:
    if len(start_indices) != len(slice_sizes):
      raise ValueError("Lengths of start_indices and slice_sizes must be"
                       "identical.")
    return libjax.lax.dynamic_slice(tensor, start_indices, slice_sizes)

  def svd(
      self,
      tensor: Tensor,
      pivot_axis: int = -1,
      max_singular_values: Optional[int] = None,
      max_truncation_error: Optional[float] = None,
      relative: Optional[bool] = False
  ) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
    return decompositions.svd(
        jnp,
        tensor,
        pivot_axis,
        max_singular_values,
        max_truncation_error,
        relative=relative)

  def qr(
      self,
      tensor: Tensor,
      pivot_axis: int = -1,
      non_negative_diagonal: bool = False
  ) -> Tuple[Tensor, Tensor]:
    return decompositions.qr(jnp, tensor, pivot_axis, non_negative_diagonal)

  def rq(
      self,
      tensor: Tensor,
      pivot_axis: int = -1,
      non_negative_diagonal: bool = False
  ) -> Tuple[Tensor, Tensor]:
    return decompositions.rq(jnp, tensor, pivot_axis, non_negative_diagonal)


  def shape_tensor(self, tensor: Tensor) -> Tensor:
    return tensor.shape

  def shape_tuple(self, tensor: Tensor) -> Tuple[Optional[int], ...]:
    return tensor.shape

  def sparse_shape(self, tensor: Tensor) -> Tuple[Optional[int], ...]:
    return self.shape_tuple(tensor)

  def shape_prod(self, values: Tensor) -> Tensor:
    return np.prod(values)

  def sqrt(self, tensor: Tensor) -> Tensor:
    return jnp.sqrt(tensor)

  def convert_to_tensor(self, tensor: Tensor) -> Tensor:
    if (not isinstance(tensor, (np.ndarray, jnp.ndarray))
        and not jnp.isscalar(tensor)):
      raise TypeError(("Expected a `jnp.array`, `np.array` or scalar. "
                       f"Got {type(tensor)}"))
    result = jnp.asarray(tensor)
    return result

  def outer_product(self, tensor1: Tensor, tensor2: Tensor) -> Tensor:
    return jnp.tensordot(tensor1, tensor2, 0,
                         precision=self.jax_precision)

  def einsum(self,
             expression: str,
             *tensors: Tensor,
             optimize: bool = True) -> Tensor:
    return jnp.einsum(expression, *tensors, optimize=optimize,
                      precision=self.jax_precision)

  def norm(self, tensor: Tensor) -> Tensor:
    return jnp.linalg.norm(tensor)

  def eye(self,
          N,
          dtype: Optional[np.dtype] = None,
          M: Optional[int] = None) -> Tensor:
    dtype = dtype if dtype is not None else jnp.float64
    return jnp.eye(N, M=M, dtype=dtype)

  def ones(self,
           shape: Tuple[int, ...],
           dtype: Optional[np.dtype] = None) -> Tensor:
    dtype = dtype if dtype is not None else jnp.float64
    return jnp.ones(shape, dtype=dtype)

  def zeros(self,
            shape: Tuple[int, ...],
            dtype: Optional[np.dtype] = None) -> Tensor:
    dtype = dtype if dtype is not None else jnp.float64
    return jnp.zeros(shape, dtype=dtype)

  def randn(self,
            shape: Tuple[int, ...],
            dtype: Optional[np.dtype] = None,
            seed: Optional[int] = None) -> Tensor:
    if not seed:
      seed = np.random.randint(0, 2**63)
    key = libjax.random.PRNGKey(seed)

    dtype = dtype if dtype is not None else np.dtype(np.float64)

    def cmplx_randn(complex_dtype, real_dtype):
      real_dtype = np.dtype(real_dtype)
      complex_dtype = np.dtype(complex_dtype)

      key_2 = libjax.random.PRNGKey(seed + 1)

      real_part = libjax.random.normal(key, shape, dtype=real_dtype)
      complex_part = libjax.random.normal(key_2, shape, dtype=real_dtype)
      unit = (
          np.complex64(1j)
          if complex_dtype == np.dtype(np.complex64) else np.complex128(1j))
      return real_part + unit * complex_part

    if np.dtype(dtype) is np.dtype(jnp.complex128):
      return cmplx_randn(dtype, jnp.float64)
    if np.dtype(dtype) is np.dtype(jnp.complex64):
      return cmplx_randn(dtype, jnp.float32)

    return libjax.random.normal(key, shape).astype(dtype)

  def random_uniform(self,
                     shape: Tuple[int, ...],
                     boundaries: Optional[Tuple[float, float]] = (0.0, 1.0),
                     dtype: Optional[np.dtype] = None,
                     seed: Optional[int] = None) -> Tensor:
    if not seed:
      seed = np.random.randint(0, 2**63)
    key = libjax.random.PRNGKey(seed)

    dtype = dtype if dtype is not None else np.dtype(np.float64)

    def cmplx_random_uniform(complex_dtype, real_dtype):
      real_dtype = np.dtype(real_dtype)
      complex_dtype = np.dtype(complex_dtype)

      key_2 = libjax.random.PRNGKey(seed + 1)

      real_part = libjax.random.uniform(
          key,
          shape,
          dtype=real_dtype,
          minval=boundaries[0],
          maxval=boundaries[1])
      complex_part = libjax.random.uniform(
          key_2,
          shape,
          dtype=real_dtype,
          minval=boundaries[0],
          maxval=boundaries[1])
      unit = (
          np.complex64(1j)
          if complex_dtype == np.dtype(np.complex64) else np.complex128(1j))
      return real_part + unit * complex_part

    if np.dtype(dtype) is np.dtype(jnp.complex128):
      return cmplx_random_uniform(dtype, jnp.float64)
    if np.dtype(dtype) is np.dtype(jnp.complex64):
      return cmplx_random_uniform(dtype, jnp.float32)

    return libjax.random.uniform(
        key, shape, minval=boundaries[0], maxval=boundaries[1]).astype(dtype)

  def eigs(self, #pylint: disable=arguments-differ
           A: Callable,
           args: Optional[List] = None,
           initial_state: Optional[Tensor] = None,
           shape: Optional[Tuple[int, ...]] = None,
           dtype: Optional[Type[np.number]] = None,
           num_krylov_vecs: int = 50,
           numeig: int = 6,
           tol: float = 1E-8,
           which: Text = 'LR',
           maxiter: int = 20) -> Tuple[Tensor, List]:
    """
    Implicitly restarted Arnoldi method for finding the lowest
    eigenvector-eigenvalue pairs of a linear operator `A`.
    `A` is a function implementing the matrix-vector
    product.

    WARNING: This routine uses jax.jit to reduce runtimes. jitting is triggered
    at the first invocation of `eigs`, and on any subsequent calls
    if the python `id` of `A` changes, even if the formal definition of `A`
    stays the same.
    Example: the following will jit once at the beginning, and then never again: