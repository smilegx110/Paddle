import unittest
import numpy as np
from op_test import OpTest


def nce(input, weight, bias, sample_weight, labels, num_classes,
        num_sample_class):
    samples = []
    sample_labels = []
    batch_size = input.shape[0]
    num_true_class = labels.shape[1]
    for i in range(batch_size):
        w = 1 if sample_weight is None else sample_weight[i]
        for label in labels[i]:
            samples.append((i, label, True, w))
            sample_labels.append(label)
        for num in range(num_sample_class):
            samples.append((i, num, False, w))
            sample_labels.append(num)
    # forward bias
    sampleOut = np.zeros(len(samples)).astype(np.float32)
    if bias is not None:
        for i in range(len(samples)):
            sampleOut[i] = bias[samples[i][1]]
    # forward weight
    for i in range(len(samples)):
        sampleOut[i] += np.dot(input[samples[i][0]], weight[samples[i][1]])

    # forward activation
    sampleOut = 1.0 / (1.0 + np.exp(-sampleOut))
    # forward cost
    out = np.zeros(batch_size).astype(np.float32)
    b = 1.0 / num_classes * num_sample_class
    for i in range(len(samples)):
        o = sampleOut[i]
        cost = -np.log(o / (o + b)) if samples[i][2] else -np.log(b / (o + b))
        out[samples[i][0]] += cost * samples[i][3]
    return (out, np.array(sampleOut).reshape(batch_size,
                                             num_sample_class + num_true_class),
            np.array(sample_labels).reshape(batch_size,
                                            num_sample_class + num_true_class))


class TestNCE(OpTest):
    def generate_data(self, dim, batch_size, num_classes, num_true_class,
                      num_sampled_classes):
        input = np.random.randn(batch_size, dim).astype(np.float32)
        weight = np.random.randn(num_classes, dim).astype(np.float32)
        bias = np.random.randn(num_classes).astype(np.float32)
        sample_weight = np.random.randn(batch_size).astype(np.float32)
        labels = np.random.randint(0, num_classes, (batch_size, num_true_class))
        self.attrs = {
            'num_classes': num_classes,
            'num_sampled_classes': num_sampled_classes,
            'sampled_labels': range(num_sampled_classes)
        }
        self.inputs = {
            'X': input,
            'Label': labels,
            'W': weight,
            'B': bias,
            'SampleWeight': sample_weight
        }

    def set_data(self):
        self.generate_data(5, 5, 4, 1, 2)

    def compute(self):
        out = nce(self.inputs['X'], self.inputs['W'], self.inputs['B'],
                  self.inputs['SampleWeight'], self.inputs['Label'],
                  self.attrs['num_classes'], self.attrs['num_sampled_classes'])
        self.outputs = {
            'Out': out[0],
            'SampleLogits': out[1],
            'SampleLabels': out[2]
        }

    def setUp(self):
        self.op_type = 'nce'
        self.set_data()
        self.compute()

    def test_check_output(self):
        self.check_output()

    def test_check_grad(self):
        self.check_grad(["X", "W", "B"], "Out", max_relative_error=0.02)


class TestNCECase1(TestNCE):
    def set_data(self):
        self.generate_data(10, 20, 10, 2, 5)


if __name__ == '__main__':
    unittest.main()
