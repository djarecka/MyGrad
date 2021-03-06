from mygrad import Tensor
from mygrad.operation_base import Operation
import mygrad as mg
from mygrad.math.arithmetic.ops import Add, Subtract, Multiply, Divide, Power
from mygrad.math.arithmetic.ops import Negative
from mygrad.linalg.ops import MatMul

from hypothesis import given
import hypothesis.strategies as st
import hypothesis.extra.numpy as hnp

from pytest import raises
import pytest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal, assert_equal


def test_to_scalar():
    nd_tensor = Tensor([1, 2])
    with raises(TypeError):
        float(nd_tensor)

    with raises(TypeError):
        int(nd_tensor)

    with raises(ValueError):
        nd_tensor.item()

    for size1_tensor in (Tensor(1), Tensor([[1]])):
        assert float(size1_tensor) == 1.
        assert int(size1_tensor) == 1
        assert size1_tensor.item() == 1.


@pytest.mark.parametrize(
    ("tensor", "repr_"),
    [(Tensor(1), 'Tensor(1)'),
     (Tensor([1]), 'Tensor([1])'),
     (Tensor([1, 2]), 'Tensor([1, 2])'),
     (mg.arange(9).reshape((3, 3)),
      'Tensor([[0, 1, 2],\n'
      '        [3, 4, 5],\n'
      '        [6, 7, 8]])')
     ]
)
def test_repr(tensor, repr_):
    assert repr(tensor) == repr_


@pytest.mark.parametrize("element", (0, [0, 1, 2]))
def test_contains(element):
    t = Tensor([[0, 1, 2], [3, 4, 5]])
    assert element in t
    assert element in t.data


@given(a=hnp.arrays(shape=hnp.array_shapes(max_side=3, max_dims=5),
                    dtype=float,
                    elements=st.floats(-100, 100)),
       constant=st.booleans(),
       scalar=st.booleans(),
       creator=st.booleans())
def test_properties(a, constant, scalar, creator):
    array = np.asarray(a)
    if creator:
        ref = Operation()
        tensor = Tensor(a, constant=constant, _creator=ref, _scalar_only=scalar)
    else:
        tensor = Tensor(a, constant=constant, _scalar_only=scalar)

    assert tensor.ndim == array.ndim
    assert tensor.shape == array.shape
    assert tensor.size == array.size
    assert len(tensor) == len(array)
    assert tensor.dtype == array.dtype
    assert_equal(actual=tensor.data, desired=a)
    assert (not creator) or tensor.creator is ref


def test_init_data():
    for data in [0, [], (0, 0), ((0, 0), (0, 0)), np.random.rand(3, 4, 2)]:
        assert_equal(actual=Tensor(data).data, desired=np.asarray(data),
                     err_msg="Initialization with non-tensor failed")
        assert_equal(actual=Tensor(Tensor(data)).data, desired=np.asarray(data),
                     err_msg="Initialization with tensor failed")


@given(x=hnp.arrays(dtype=float, shape=hnp.array_shapes(min_dims=1, max_dims=4)))
def test_init_data_rand(x):
    assert_equal(actual=Tensor(x).data, desired=x)


@given(x=hnp.arrays(dtype=float, shape=hnp.array_shapes()))
def test_items(x):
    """ verify that tensor.item() mirrors array.item()"""
    tensor = Tensor(x)
    try:
        value = x.item()
        assert_allclose(value, tensor.item())
    except ValueError:
        with raises(ValueError):
            tensor.item()


op = Operation()
dtype_strat = st.sampled_from((None, int, float,
                               np.int8, np.int16, np.int32, np.int64,
                               np.float16, np.float32, np.float64))
dtype_strat_numpy = st.sampled_from((np.int8, np.int16, np.int32, np.int64,
                                     np.float16, np.float32, np.float64))


@given(data=st.data(),
       creator=st.sampled_from((None, op)),
       constant=st.booleans(),
       scalar_only=st.booleans(),
       dtype=dtype_strat,
       numpy_dtype=dtype_strat_numpy)
def test_init_params(data, creator, constant, scalar_only, dtype, numpy_dtype):
    elements = st.floats if np.issubdtype(numpy_dtype, np.floating) else st.integers
    a = data.draw(hnp.arrays(shape=hnp.array_shapes(max_side=3, max_dims=5),
                             dtype=numpy_dtype,
                             elements=elements(-100, 100)),
                  label="a")
    if dtype is not None:
        a = a.astype(dtype)

    tensor = Tensor(a, _creator=creator, constant=constant, _scalar_only=scalar_only, dtype=dtype)

    assert tensor.creator is creator
    assert tensor.constant is constant
    assert tensor.scalar_only is scalar_only
    assert tensor.dtype is a.dtype
    assert_equal(tensor.data, a)
    assert tensor.grad is None


@pytest.mark.parametrize(
    ("op_name", "op"),
    [("add", Add),
     ("sub", Subtract),
     ("mul", Multiply),
     ("truediv", Divide),
     ("pow", Power),
     ("matmul", MatMul),
     ])
@pytest.mark.parametrize("right_op", [True, False])
@given(constant_x=st.booleans(), constant_y=st.booleans())
def test_special_methods(op_name: str, op: Operation,
                         constant_x: bool, constant_y: bool, right_op: bool):
    if right_op:
        op_name = "r" + op_name
    op_name = "__" + op_name + "__"
    x = Tensor([2., 8., 5.], constant=constant_x)
    y = Tensor([1., 3., 2.], constant=constant_y)

    constant = constant_x and constant_y
    assert hasattr(Tensor, op_name)
    tensor_out = getattr(Tensor, op_name)(x, y)
    numpy_out = getattr(np.ndarray, op_name)(x.data, y.data)
    assert isinstance(tensor_out, Tensor)
    assert tensor_out.constant is constant
    assert_equal(tensor_out.data, numpy_out)
    assert isinstance(tensor_out.creator, op)

    if not right_op:
        assert tensor_out.creator.variables[0] is x
        assert tensor_out.creator.variables[1] is y
    else:
        assert tensor_out.creator.variables[0] is y
        assert tensor_out.creator.variables[1] is x


@given(x=hnp.arrays(shape=hnp.array_shapes(), dtype=hnp.floating_dtypes()))
def test_neg(x):
    x = Tensor(x)
    op_name = "__neg__"
    assert hasattr(Tensor, op_name)
    tensor_out = getattr(Tensor, "__neg__")(x)
    numpy_out = getattr(np.ndarray, "__neg__")(x.data)
    assert isinstance(tensor_out, Tensor)
    assert_equal(tensor_out.data, numpy_out)
    assert isinstance(tensor_out.creator, Negative)
    assert tensor_out.creator.variables[0] is x


@pytest.mark.parametrize("op", ("__lt__", "__le__", "__gt__", "__ge__", "__eq__", "__ne__"))
@given(x=hnp.arrays(shape=hnp.array_shapes(),
                    dtype=hnp.floating_dtypes(),
                    elements=st.floats(-10, 10)),
       x_constant=st.booleans(),
       y_constant=st.booleans(),
       data=st.data())
def test_comparison_ops(op: str, x: np.ndarray,
                        x_constant: bool,
                        y_constant: bool,
                        data: st.SearchStrategy):
    y = data.draw(hnp.arrays(shape=x.shape, dtype=x.dtype, elements=st.floats(-10, 10)))
    x = Tensor(x, constant=x_constant)
    y = Tensor(y, constant=y_constant)
    assert hasattr(Tensor, op), "`Tensor` is missing the attribute {}".format(op)
    tensor_out = getattr(Tensor, op)(x, y)
    array_out = getattr(np.ndarray, op)(x.data, y.data)
    assert_equal(actual=tensor_out, desired=array_out)


@pytest.mark.parametrize(
    "attr",
    ("sum",
     "prod",
     "cumprod",
     "cumsum",
     "mean",
     "std",
     "var",
     "max",
     "min",
     "transpose",
     "squeeze",
     "ravel"))
@given(constant=st.booleans())
def test_math_methods(attr: str, constant: bool):
    x = Tensor([[1., 2., 3.],
                [4., 5., 6.]], constant=constant)

    assert hasattr(x, attr)
    method_out = getattr(x, attr).__call__()
    function_out = getattr(mg, attr).__call__(x)
    assert_equal(method_out.data, function_out.data)
    assert method_out.constant is constant
    assert type(method_out.creator) is type(function_out.creator)


@pytest.mark.parametrize("op", ("moveaxis", "swapaxes"))
@given(constant=st.booleans())
def test_axis_interchange_methods(op: str, constant: bool):
    x = Tensor([[1., 2., 3.],
                [4., 5., 6.]], constant=constant)
    method_out = getattr(x, op)(0, -1)
    function_out = getattr(mg, op)(x, 0, -1)
    assert_equal(method_out.data, function_out.data)
    assert method_out.constant is constant
    assert type(method_out.creator) is type(function_out.creator)


@given(x=st.floats(min_value=-1E6, max_value=1E6),
       y=st.floats(min_value=-1E6, max_value=1E6),
       z=st.floats(min_value=-1E6, max_value=1E6),
       clear_graph=st.booleans())
def test_null_gradients(x, y, z, clear_graph):
    x = Tensor(x)
    y = Tensor(y)
    z = Tensor(z)

    f = x*y + z
    g = x + z*f*f

    # check side effects
    unused = 2*g - f
    w = 1*f

    g.backward()
    assert x.grad is not None
    assert y.grad is not None
    assert z.grad is not None
    assert f.grad is not None
    assert g.grad is not None
    assert len(x._ops) > 0
    assert len(y._ops) > 0
    assert len(z._ops) > 0
    assert len(f._ops) > 0
    assert len(g._ops) > 0
    assert w.grad is None

    g.null_gradients(clear_graph=clear_graph)
    assert x.grad is None
    assert y.grad is None
    assert z.grad is None
    assert f.grad is None
    assert g.grad is None

    if clear_graph:
        assert len(x._ops) == 0
        assert len(y._ops) == 0
        assert len(z._ops) == 0
        assert len(f._ops) == 0
        assert len(g._ops) > 0
        assert x.creator is None
        assert y.creator is None
        assert z.creator is None
        assert f.creator is None
        assert g.creator is None
    else:
        assert len(x._ops) > 0
        assert len(y._ops) > 0
        assert len(z._ops) > 0
        assert len(f._ops) > 0
        assert len(g._ops) > 0
        assert x.creator is None
        assert y.creator is None
        assert z.creator is None
        assert f.creator is not None
        assert g.creator is not None


@given(x=st.floats(min_value=-1E-6, max_value=1E6),
       y=st.floats(min_value=-1E-6, max_value=1E6),
       z=st.floats(min_value=-1E-6, max_value=1E6))
def test_clear_graph(x, y, z):
    x_orig = x
    y_orig = y
    z_orig = z

    x = Tensor(x)
    y = Tensor(y)
    z = Tensor(z)

    f = x*y + z
    g = x + z*f*f

    # check side effects
    unused = 2*g - f
    w = 1*f

    g.backward()
    assert_allclose(f.grad, 2 * z.data * f.data)
    assert_allclose(x.grad, 1 + 2 * z.data * f.data * y.data)
    assert_allclose(y.grad, 2 * z.data * f.data * x.data)
    assert_allclose(z.grad, f.data**2 + z.data * 2 * f.data)
    assert w.grad is None

    assert_array_equal(x.data, x_orig, err_msg="x was mutated during the operation")
    assert_array_equal(y.data, y_orig, err_msg="y was mutated during the operation")
    assert_array_equal(z.data, z_orig, err_msg="z was mutated during the operation")

    # null-gradients without clearing the graph, confirm that backprop still works
    g.null_gradients(clear_graph=False)
    g.backward()
    assert_allclose(f.grad, 2 * z.data * f.data)
    assert_allclose(x.grad, 1 + 2 * z.data * f.data * y.data)
    assert_allclose(y.grad, 2 * z.data * f.data * x.data)
    assert_allclose(z.grad, f.data**2 + z.data * 2 * f.data)
    assert w.grad is None

    assert_array_equal(x.data, x_orig, err_msg="x was mutated during the operation")
    assert_array_equal(y.data, y_orig, err_msg="y was mutated during the operation")
    assert_array_equal(z.data, z_orig, err_msg="z was mutated during the operation")

    g.null_gradients(clear_graph=False)
    w.backward()
    assert_allclose(x.grad, y.data)
    assert_allclose(y.grad, x.data)
    assert_allclose(z.grad, np.array(1.))

    w.clear_graph()
    assert_allclose(x.grad, y.data)
    assert_allclose(y.grad, x.data)
    assert_allclose(z.grad, np.array(1.))
    assert len(g._ops) > 0
    assert g.creator is not None
    assert len(x._ops) == 0
    assert len(y._ops) == 0
    assert len(z._ops) == 0
    assert len(f._ops) == 0
    assert x.creator is None
    assert y.creator is None
    assert z.creator is None
    assert f.creator is None

    with raises(Exception):
        g.backward()
