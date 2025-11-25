# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Various learning rate decay functions."""

import abc
import math

from tensorflow.python.framework import constant_op
from tensorflow.python.framework import ops
from tensorflow.python.keras.utils import generic_utils
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import random_ops
from tensorflow.python.util import nest
from tensorflow.python.util.tf_export import keras_export


@keras_export("keras.optimizers.schedules.LearningRateSchedule")
class LearningRateSchedule(object):
  """The learning rate schedule base class.

  You can use a learning rate schedule to modulate how the learning rate
  of your optimizer changes over time.

  Several built-in learning rate schedules are available, such as
  `tf.keras.optimizers.schedules.ExponentialDecay` or
  `tf.keras.optimizers.schedules.PiecewiseConstantDecay`: