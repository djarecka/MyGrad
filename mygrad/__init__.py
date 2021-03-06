from mygrad.tensor_base import Tensor
from mygrad.math.arithmetic.funcs import *
from mygrad.math.exp_log.funcs import *
from mygrad.math.trigonometric.funcs import *
from mygrad.math.hyperbolic_trig.funcs import *
from mygrad.math.sequential.funcs import *
from mygrad.math.sequential.funcs import max, min
from mygrad.math.nondifferentiable import argmax, argmin
from mygrad.math.misc.funcs import *
from mygrad.tensor_manip.array_shape.funcs import *
from mygrad.tensor_manip.transpose_like.funcs import *
from mygrad.tensor_creation.funcs import *
from mygrad.linalg.funcs import *

from mygrad.nnet.layers.utils import sliding_window_view

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions


for attr in (sum, prod, cumprod, cumsum,
             mean, std, var,
             max, min,
             argmax, argmin,
             swapaxes, transpose, moveaxis,
             reshape, squeeze, ravel,
             matmul):
    setattr(Tensor, attr.__name__, attr)
