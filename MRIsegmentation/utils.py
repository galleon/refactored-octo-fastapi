import tensorflow as tf
import tensorflow.keras.backend as K


def tversky(y_true, y_pred, smooth=1.0e-7, alpha=0.7, beta=0.3):
    """
    Compute the Tversky score.

    The Tversky index, named after Amos Tversky, is an asymmetric similarity measure on sets
    that compares a prediction to a ground truth.

    :y_true: the ground truth mask
    :y_pred: the predicted mask
    :return: The tversky score
    :rtype: float

    :Example:

    >>> tversky([0, 0, 0], [1, 1, 1])
    smooth / (smooth + 3*alpha)
    >>> tversky([1, 1, 1], [1, 1, 1]))
    1

    .. seealso:: tensorflow.keras.metrics.MeanIoU
                 https://en.wikipedia.org/wiki/Tversky_index
    .. warning:: smooth needs to adapt to the size of the mask
    .. note:: Setting alpha=beta=0.5 produces the Sørensen–Dice coefficient.
              alpha=beta=1 produces the Tanimoto coefficient aka Jaccard index
    .. todo:: Better understand how to set the parameters
    """
    y_true_pos = K.flatten(y_true)
    y_pred_pos = K.flatten(y_pred)
    true_pos = K.sum(y_true_pos * y_pred_pos)
    false_neg = K.sum(y_true_pos * (1 - y_pred_pos))
    false_pos = K.sum((1 - y_true_pos) * y_pred_pos)

    return (true_pos + smooth) / (
        true_pos + alpha * false_neg + beta * false_pos + smooth
    )


def focal_tversky(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)

    pt_1 = tversky(y_true, y_pred)
    gamma = 0.75
    return K.pow((1 - pt_1), gamma)
