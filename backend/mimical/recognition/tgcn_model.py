import math

import torch
import torch.nn as nn
from torch.nn.parameter import Parameter


class GraphConvolutionAtt(nn.Module):
    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.weight = Parameter(torch.FloatTensor(in_features, out_features))
        self.att = Parameter(torch.FloatTensor(55, 55))
        if bias:
            self.bias = Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter("bias", None)
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1.0 / math.sqrt(self.weight.size(1))
        self.weight.data.uniform_(-stdv, stdv)
        self.att.data.uniform_(-stdv, stdv)
        if self.bias is not None:
            self.bias.data.uniform_(-stdv, stdv)

    def forward(self, inputs):
        support = torch.matmul(inputs, self.weight)
        output = torch.matmul(self.att, support)
        if self.bias is not None:
            return output + self.bias
        return output


class GCBlock(nn.Module):
    def __init__(self, in_features, p_dropout, is_residual=True):
        super().__init__()
        self.is_residual = is_residual
        self.gc1 = GraphConvolutionAtt(in_features, in_features)
        self.bn1 = nn.BatchNorm1d(55 * in_features)
        self.gc2 = GraphConvolutionAtt(in_features, in_features)
        self.bn2 = nn.BatchNorm1d(55 * in_features)
        self.dropout = nn.Dropout(p_dropout)
        self.activation = nn.Tanh()

    def forward(self, inputs):
        outputs = self.gc1(inputs)
        batch_size, node_count, feature_count = outputs.shape
        outputs = self.bn1(outputs.view(batch_size, -1)).view(batch_size, node_count, feature_count)
        outputs = self.activation(outputs)
        outputs = self.dropout(outputs)

        outputs = self.gc2(outputs)
        batch_size, node_count, feature_count = outputs.shape
        outputs = self.bn2(outputs.view(batch_size, -1)).view(batch_size, node_count, feature_count)
        outputs = self.activation(outputs)
        outputs = self.dropout(outputs)

        if self.is_residual:
            return outputs + inputs
        return outputs


class GCNMultiAtt(nn.Module):
    def __init__(self, input_feature, hidden_feature, num_class, p_dropout, num_stage=1):
        super().__init__()
        self.gc1 = GraphConvolutionAtt(input_feature, hidden_feature)
        self.bn1 = nn.BatchNorm1d(55 * hidden_feature)
        self.blocks = nn.ModuleList(
            [GCBlock(hidden_feature, p_dropout=p_dropout, is_residual=True) for _ in range(num_stage)]
        )
        self.dropout = nn.Dropout(p_dropout)
        self.activation = nn.Tanh()
        self.fc_out = nn.Linear(hidden_feature, num_class)

    def forward(self, inputs):
        outputs = self.gc1(inputs)
        batch_size, node_count, feature_count = outputs.shape
        outputs = self.bn1(outputs.view(batch_size, -1)).view(batch_size, node_count, feature_count)
        outputs = self.activation(outputs)
        outputs = self.dropout(outputs)

        for block in self.blocks:
            outputs = block(outputs)

        outputs = torch.mean(outputs, dim=1)
        return self.fc_out(outputs)

